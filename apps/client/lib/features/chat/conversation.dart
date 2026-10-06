// 대화 하나의 상태와 멈춤 처리 (docs/plan/06-api-spec.md 2·3장).
//   question  사용자가 답한다 (입력창 또는 선택 버튼)
//   approval  사용자가 승인·거절·수정한다 (처리안 카드·상세 화면)
//   fetch     앱이 증권사에서 조회해서 자동으로 답한다
//   execute   앱이 가격을 다시 확인하고 주문해서 결과를 자동으로 답한다
// 대화 화면과 승인 대기 화면이 같은 로직을 쓴다.

import 'package:flutter/foundation.dart';

import '../../api/api.dart';
import '../../broker/broker.dart';

class ChatItem {
  ChatItem(this.role, this.text, {this.interrupt});
  final String role; // user / assistant / info / error
  final String text;
  final Map<String, dynamic>? interrupt; // question·approval 멈춤이면 선택 버튼·처리안 카드를 그린다
}

class Conversation extends ChangeNotifier {
  Conversation({this.threadId, this.waiting});

  String? threadId;
  final items = <ChatItem>[];
  String? progress; // "투자 AI 분석 중" 같은 진행 단계
  bool busy = false;
  Map<String, dynamic>? waiting; // 사용자 답을 기다리는 멈춤 (question / approval / 웹의 execute)

  /// 입력창: 질문·처리안을 기다리는 중이면 그에 대한 답, 아니면 새 요청
  Future<void> submit(String text) {
    final kind = waiting?['kind'];
    if (kind == 'question') return answer({'text': text}, shown: text);
    if (kind == 'approval') return answer({'decision': 'edit', 'text': text}, shown: text);
    return send(text);
  }

  Future<void> send(String text) {
    items.add(ChatItem('user', text));
    waiting = null; // 서버도 멈춰 있던 업무를 버리고 새로 시작한다
    return _run(api.stream('/api/chat', {'thread_id': threadId, 'text': text, 'client': clientKind}));
  }

  /// 지금 기다리는 멈춤에 답한다. shown: 대화에 보여줄 사용자 말
  Future<void> answer(Map<String, dynamic> payload, {String? shown}) {
    final interruptId = waiting!['interrupt_id'];
    waiting = null;
    if (shown != null) items.add(ChatItem('user', shown));
    return _run(api.stream('/api/chat/resume', {
      'thread_id': threadId,
      'interrupt_id': interruptId,
      'payload': payload,
      'client': clientKind,
    }));
  }

  Future<void> _run(Stream<SseEvent> events) async {
    busy = true;
    notifyListeners();
    try {
      await for (final e in events) {
        switch (e.event) {
          case 'progress':
            progress = e.data['label'] as String;
          case 'message':
            items.add(ChatItem('assistant', e.data['text'] as String));
          case 'error':
            items.add(ChatItem('error', e.data['detail'] as String));
          case 'done':
            threadId = e.data['thread_id'] as String;
          case 'interrupt':
            _onInterrupt(e.data);
        }
        notifyListeners();
      }
    } on ApiError catch (error) {
      items.add(ChatItem('error', error.message));
    }
    progress = null;
    busy = false;
    notifyListeners();
    // fetch·execute는 스트림이 끝난 뒤 앱이 증권사에 다녀와서 바로 답한다
    final kind = waiting?['kind'];
    if (kind == 'fetch') await answer(await answerFetch(currentBroker.value, waiting!['needs'] as List));
    if (kind == 'execute' && !kIsWeb) await executeWaiting();
  }

  void _onInterrupt(Map<String, dynamic> data) {
    final kind = data['kind'];
    waiting = data;
    final brokerName = currentBroker.value?.name ?? '증권사';
    if (kind == 'fetch') {
      items.add(ChatItem('info', '$brokerName에서 잔고·시세 확인 중…'));
    } else if (kind == 'execute') {
      if (kIsWeb) {
        items.add(ChatItem('info', '승인했어요. 주문 실행은 폰 앱에서 해 주세요.'));
        waiting = null;
      } else {
        final steps = currentBroker.value?.isFake ?? true ? '가격 재확인 → 주문' : '가격 재확인 → 폰 잠금 확인 → 주문';
        items.add(ChatItem('info', '$brokerName에 주문하는 중… ($steps)'));
      }
    } else {
      items.add(ChatItem('assistant', data['text'] as String, interrupt: data));
    }
  }

  /// execute 멈춤: 가격 재확인 → 폰 잠금 확인 → 주문 → 결과. 승인 대기의 "실행 필요"에서도 부른다
  Future<void> executeWaiting() async {
    final request = waiting!['request'] as Map<String, dynamic>;
    final result = await executeOrder(currentBroker.value, request, unlock: phoneUnlock, journal: orderJournal);
    await answer({'result': result});
  }

  /// 처리안 카드가 아직 답을 기다리는지 (이미 답한 카드의 버튼은 끈다)
  bool isWaiting(Map<String, dynamic>? interrupt) =>
      interrupt != null && waiting?['interrupt_id'] == interrupt['interrupt_id'] && !busy;
}
