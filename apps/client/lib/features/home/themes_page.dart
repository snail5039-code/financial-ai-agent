// 종목 탭: 주제별(반도체, 2차전지 …) 분석 대상 종목. 주제는 직접 나눈 것이고 가격은 전 거래일 종가 (GET /api/themes).
// 종목을 누르면 그 종목 대화방.

import 'package:flutter/material.dart';

import '../../api/api.dart';
import '../../common/common.dart';
import '../chat/chat_page.dart';
import '../chat/conversation.dart';
import 'equity_chart.dart';

/// 등락률 표시: +1.23% / -0.10% / 미확인
String changeText(num? pct) => pct == null ? '미확인' : '${pct > 0 ? '+' : ''}${pct.toStringAsFixed(2)}%';

class ThemesPage extends StatefulWidget {
  const ThemesPage({super.key});

  @override
  State<ThemesPage> createState() => _ThemesPageState();
}

class _ThemesPageState extends State<ThemesPage> {
  late Future<List<Map<String, dynamic>>> _themes = _load();
  int _picked = 0;

  Future<List<Map<String, dynamic>>> _load() async => (await api.get('/api/themes') as List).cast<Map<String, dynamic>>();

  Future<void> _openRoom(String code, String name) async {
    final room = Conversation(stockCode: code, stockName: name);
    try {
      await room.loadRoom();
    } on ApiError catch (error) {
      if (mounted) showError(context, error);
      return;
    }
    if (mounted) await Navigator.of(context).push(pageRoute(ChatPage(room)));
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: topBar('종목'),
        body: FutureBuilder(
          future: _themes,
          builder: (context, snapshot) {
            if (snapshot.hasError) return ErrorRetry(snapshot.error!, () => setState(() => _themes = _load()));
            final themes = snapshot.data;
            if (themes == null) return const Center(child: CircularProgressIndicator());
            if (themes.isEmpty) return const Center(child: Text('분석 대상 종목이 아직 없어요', style: TextStyle(color: mutedText)));
            final picked = themes[_picked.clamp(0, themes.length - 1)];
            final stocks = (picked['stocks'] as List).cast<Map<String, dynamic>>();
            final day = stocks.map((s) => s['trade_date'] as String?).whereType<String>().fold<String?>(
                null, (a, b) => a == null || b.compareTo(a) > 0 ? b : a);
            return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              SizedBox(
                height: 48,
                child: ListView(scrollDirection: Axis.horizontal, padding: const EdgeInsets.symmetric(horizontal: 12), children: [
                  for (final (i, theme) in themes.indexed)
                    Padding(
                      padding: const EdgeInsets.only(right: 6),
                      child: ChoiceChip(
                        label: Text('${theme['theme']} ${(theme['stocks'] as List).length}'),
                        selected: i == _picked,
                        onSelected: (_) => setState(() => _picked = i),
                      ),
                    ),
                ]),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 2, 16, 6),
                child: SourceText('주제는 직접 나눈 것 · 가격은 ${day == null ? '미확인' : '${monthDay(day)} 종가'}'
                    ' (금융위원회, 실시간 아님) · 전 거래일 대비'),
              ),
              Expanded(
                child: RefreshIndicator(
                  onRefresh: () async {
                    final next = _load();
                    setState(() => _themes = next);
                    await next;
                  },
                  child: ListView(children: [
                    for (final s in stocks)
                      ListTile(
                        title: Text(s['name'] as String, style: const TextStyle(fontWeight: FontWeight.bold)),
                        subtitle: Text('${s['market'] == 'KOSDAQ' ? '코스닥' : '코스피'} · ${s['code']}'),
                        trailing: Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.end, children: [
                          Text(s['close'] == null ? '미확인' : '${comma(s['close'] as int)}원', style: const TextStyle(fontWeight: FontWeight.bold)),
                          Text(changeText(s['change_pct'] as num?),
                              style: TextStyle(fontSize: 12, color: changeColor((s['change_pct'] as num?) ?? 0) ?? mutedText)),
                        ]),
                        onTap: () => _openRoom(s['code'] as String, s['name'] as String),
                      ),
                  ]),
                ),
              ),
            ]);
          },
        ),
      );
}
