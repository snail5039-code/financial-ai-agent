// 아침 브리핑 (docs/plan/12-todo-by-stage.md 1-1): 오늘의 매수 제안 · 보유 종목 소식 · 오늘 한도.
// 매수 제안은 투자 AI → 검증 AI를 거친 것이다. "주문하기"는 평소 주문 흐름(처리안 → 승인 → 폰 실행)을 시작한다.

import 'package:flutter/material.dart';

import '../../common/common.dart';
import '../history/history_page.dart';

const briefingColor = Color(0xFFFFB020);

/// 대화방 목록에 쓰는 한 줄 요약
String briefingPreview(Map<String, dynamic> briefing, {required bool today}) {
  final content = briefing['content'] as Map<String, dynamic>;
  final picks = content['picks'] as List;
  final news = content['news'] as List;
  if (!today) return '${_dateLabel(briefing['brief_date'] as String)} 브리핑';
  if (picks.isNotEmpty) return '오늘의 매수 제안 ${picks.length}개가 왔어요';
  if (news.isNotEmpty) return '보유 종목 공시 ${news.length}건이 있어요';
  return '오늘 아침 브리핑이 왔어요';
}

String _dateLabel(String ymd) {
  final d = DateTime.parse(ymd);
  return '${d.month}월 ${d.day}일';
}

class BriefingPage extends StatelessWidget {
  const BriefingPage(this.briefing, {super.key, required this.onAsk});
  final Map<String, dynamic> briefing;
  final void Function(String text) onAsk;

  @override
  Widget build(BuildContext context) {
    final content = briefing['content'] as Map<String, dynamic>;
    final picks = (content['picks'] as List).cast<Map<String, dynamic>>();
    final news = (content['news'] as List).cast<Map<String, dynamic>>();
    final checked = (content['checked'] as List).cast<Map<String, dynamic>>();
    final limits = content['limits'] as Map<String, dynamic>;
    final custom = content['mode'] == 'custom';

    return Scaffold(
      backgroundColor: const Color(0xFFFFFAF0),
      appBar: topBar('아침 브리핑',
          avatar: const RoomAvatar(icon: Icons.wb_sunny_outlined, color: briefingColor, size: 36),
          subtitle: '${_dateLabel(briefing['brief_date'] as String)} · ${hhmm(briefing['created_at'] as String)} 작성'),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        _title('오늘의 매수 제안'),
        if (!custom)
          _note('일반 모드라 매수 제안은 하지 않아요. 성향 퀴즈를 하면 맞춤 제안을 받을 수 있어요.')
        else if (picks.isEmpty)
          _note(checked.isEmpty
              ? '최근 공시가 있는 후보 종목이 없어 오늘은 제안이 없어요.'
              : '${checked.map((c) => c['stock_name']).join(', ')}을(를) 분석했지만 검증을 통과한 매수 제안이 없어요.')
        else
          for (final pick in picks) _pickCard(context, pick),
        const SizedBox(height: 20),
        _title('보유 종목 소식'),
        if (news.isEmpty) _note('최근 3일 동안 보유 종목의 새 공시가 없어요.'),
        for (final n in news)
          Card(
            color: Colors.white,
            child: ListTile(
              title: Text('${n['stock_name']} · ${n['title']}', style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: SourceText('DART 공시 · ${n['filed_at']} · ${n['url']}'),
            ),
          ),
        const SizedBox(height: 20),
        _title('오늘 한도'),
        Card(
          color: Colors.white,
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('1일 주문 한도 ${won(limits['daily_limit_krw'] as int)}', style: const TextStyle(fontWeight: FontWeight.bold)),
              Text('규칙에 걸린 요청 없이 ${limits['clean_days']}일째', style: const TextStyle(color: Color(0xFF137A33))),
            ]),
          ),
        ),
        const SizedBox(height: 16),
        const SourceText('투자 판단과 책임은 본인에게 있어요. 제안은 참고용이며 손실이 날 수 있어요. 시세는 하루 늦은 종가 기준이에요.'),
      ]),
    );
  }

  Widget _title(String text) => Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: Text(text, style: const TextStyle(fontFamily: displayFont, fontSize: 20)),
      );

  Widget _note(String text) => Card(
        color: Colors.white,
        child: Padding(padding: const EdgeInsets.all(16), child: Text(text, style: const TextStyle(color: mutedText))),
      );

  Widget _pickCard(BuildContext context, Map<String, dynamic> pick) {
    final approved = pick['verdict'] == 'approve';
    final name = pick['stock_name'] as String;
    return Card(
      color: Colors.white,
      clipBehavior: Clip.antiAlias,
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 14, 16, 8),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Expanded(child: Text('$name 매수 검토', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900))),
              Tag(approved ? '검증 승인' : '검증 조건부', approved ? const Color(0xFF137A33) : const Color(0xFF8A5A00)),
            ]),
            if (pick['last_close'] != null)
              Text('${pick['close_date']} 종가 ${won(pick['last_close'] as int)} · 1주가 10% 내리면 −${won(pick['worst_case_loss'] as int)}',
                  style: const TextStyle(fontSize: 13, color: mutedText)),
            const SizedBox(height: 8),
            for (final claim in (pick['claims'] as List).cast<Map<String, dynamic>>())
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Text('· (${claim['type']}) ${claim['text']}'
                    '${(claim['sources'] as List).isEmpty ? '' : ' [${(claim['sources'] as List).join(', ')}]'}'),
              ),
            for (final risk in (pick['risks'] as List).cast<String>())
              Text('· 위험: $risk', style: const TextStyle(color: downBlue)),
            for (final condition in (pick['conditions'] as List).cast<String>())
              Text('· 조건: $condition', style: const TextStyle(color: Color(0xFF8A5A00))),
            const SizedBox(height: 6),
            Text('검증 AI: ${pick['summary']}', style: const TextStyle(fontSize: 13, color: mutedText)),
          ]),
        ),
        const Divider(height: 1),
        Row(children: [
          Expanded(
            child: TextButton(
              onPressed: () => Navigator.of(context).push(pageRoute(HistoryDetailPage(pick['proposal_id'] as String, name))),
              child: const Text('근거 자세히'),
            ),
          ),
          const SizedBox(height: 44, child: VerticalDivider(width: 1)),
          Expanded(
            child: TextButton(
              onPressed: () {
                Navigator.of(context).pop();
                onAsk('$name 1주 사줘'); // 처리안 → 승인 → 폰 실행. 수량은 처리안에서 "2주만"처럼 바꾼다
              },
              child: const Text('주문하기', style: TextStyle(fontWeight: FontWeight.w900)),
            ),
          ),
        ]),
      ]),
    );
  }
}
