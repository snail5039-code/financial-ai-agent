// S-06 대화: 메시지, 진행 단계, 질문 선택 버튼, 처리안 카드

import 'package:flutter/material.dart';

import '../../common/common.dart';
import '../approvals/approval_detail_page.dart';
import 'conversation.dart';

class ChatPage extends StatefulWidget {
  const ChatPage(this.conversation, {super.key});
  final Conversation conversation;

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  final _input = TextEditingController();
  final _scroll = ScrollController();

  Conversation get _c => widget.conversation;

  void _submit() {
    final text = _input.text.trim();
    if (text.isEmpty || _c.busy) return;
    _input.clear();
    _c.submit(text);
  }

  void _newChat() => setState(() {
        _c.threadId = null;
        _c.waiting = null;
        _c.items.clear();
      });

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: topBar('대화', actions: [
          IconButton(tooltip: '새 대화', icon: const Icon(Icons.add_comment_outlined), onPressed: _newChat),
        ]),
        body: ListenableBuilder(
          listenable: _c,
          builder: (context, _) {
            WidgetsBinding.instance.addPostFrameCallback((_) {
              if (_scroll.hasClients) _scroll.jumpTo(_scroll.position.maxScrollExtent);
            });
            return Column(children: [
              Expanded(
                child: _c.items.isEmpty
                    ? _suggestions()
                    : ListView(controller: _scroll, padding: const EdgeInsets.all(12), children: [
                        for (final item in _c.items) _bubble(item),
                        if (_c.progress != null) _progress(_c.progress!),
                      ]),
              ),
              _inputBar(),
            ]);
          },
        ),
      );

  Widget _suggestions() => Center(
        child: Wrap(spacing: 8, children: [
          for (final text in ['잔고 보여줘', '삼성전자 사도 돼?', '기아 2주 사줘'])
            ActionChip(label: Text(text), onPressed: () => _c.send(text)),
        ]),
      );

  Widget _progress(String label) => Padding(
        padding: const EdgeInsets.all(8),
        child: Row(children: [
          const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)),
          const SizedBox(width: 8),
          Text('$label…', style: const TextStyle(color: Colors.grey)),
        ]),
      );

  Widget _bubble(ChatItem item) {
    final scheme = Theme.of(context).colorScheme;
    final mine = item.role == 'user';
    final color = switch (item.role) {
      'user' => scheme.primaryContainer,
      'error' => Colors.red.withValues(alpha: 0.12),
      'info' => scheme.surfaceContainerHighest,
      _ => scheme.surfaceContainer,
    };
    final interrupt = item.interrupt;
    return Align(
      alignment: mine ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.all(12),
        constraints: const BoxConstraints(maxWidth: 520),
        decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(12)),
        child: interrupt?['kind'] == 'approval'
            ? _approvalCard(interrupt!)
            : Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(item.text, style: item.role == 'info' ? const TextStyle(color: Colors.grey) : null),
                if (interrupt?['choices'] != null)
                  Wrap(spacing: 8, children: [
                    for (final choice in (interrupt!['choices'] as List).cast<Map<String, dynamic>>())
                      OutlinedButton(
                        onPressed: _c.isWaiting(interrupt)
                            ? () => _c.answer({'choice_id': choice['id']}, shown: choice['label'] as String)
                            : null,
                        child: Text(choice['label'] as String),
                      ),
                  ]),
              ]),
      ),
    );
  }

  /// 처리안 카드: 종목, 매수/매도, 수량, 금액, 검증 판정 + [자세히] [거절] [승인]
  Widget _approvalCard(Map<String, dynamic> interrupt) {
    final card = interrupt['card'] as Map<String, dynamic>;
    final open = _c.isWaiting(interrupt);
    final needsConfirm = (interrupt['confirm_required'] as List).isNotEmpty;
    void detail() => Navigator.of(context).push(MaterialPageRoute(
        builder: (_) => ApprovalDetailPage(card: card, conversation: open ? _c : null, interrupt: interrupt)));

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [
        const Text('처리안', style: TextStyle(fontWeight: FontWeight.bold)),
        const Spacer(),
        VerdictTag(card['verdict'] as String),
      ]),
      const SizedBox(height: 4),
      Text('${card['stock_name']} ${comma(card['qty'] as int)}주 ${sideLabels[card['side']]}',
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
      Text('지정가 ${won(card['limit_price'] as int)} · 예상 ${won(card['amount'] as int)}'),
      if (needsConfirm) const Text('확인이 필요한 위험이 있어요', style: TextStyle(color: Colors.orange)),
      if (open) Text('${hhmm(interrupt['expires_at'] as String)}까지 · 바꾸려면 "2주만"처럼 입력하세요',
          style: const TextStyle(fontSize: 12, color: Colors.grey)),
      const SizedBox(height: 8),
      Wrap(spacing: 8, children: [
        OutlinedButton(onPressed: detail, child: const Text('자세히')),
        if (open) OutlinedButton(
          onPressed: () => _c.answer({'decision': 'reject'}, shown: '거절'),
          child: const Text('거절'),
        ),
        if (open) FilledButton(
          // 확인이 필요한 위험이 있으면 상세 화면에서 내용을 보고 확인해야 승인할 수 있다
          onPressed: needsConfirm ? detail : () => _c.answer({'decision': 'approve'}, shown: '승인'),
          child: const Text('승인'),
        ),
      ]),
    ]);
  }

  Widget _inputBar() {
    final kind = _c.waiting?['kind'];
    final hint = kind == 'question' ? '답을 입력하세요' : kind == 'approval' ? '수정할 내용 (예: 2주만)' : '무엇이든 물어보세요';
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: Row(children: [
          Expanded(
            child: TextField(
              controller: _input,
              decoration: InputDecoration(hintText: hint, border: const OutlineInputBorder()),
              onSubmitted: (_) => _submit(),
            ),
          ),
          IconButton(icon: const Icon(Icons.send), onPressed: _c.busy ? null : _submit),
        ]),
      ),
    );
  }
}
