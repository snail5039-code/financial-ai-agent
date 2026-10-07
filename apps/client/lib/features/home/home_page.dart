// 오늘 탭 (S-05 홈, 디자인 H안): 큰 링, 계좌 요약, 보유 종목, 바로 물어보기

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../../common/common.dart';
import '../settings/broker_page.dart';
import 'overview.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key, required this.onAsk, required this.active});
  final void Function(String text) onAsk;
  final bool active; // 탭으로 돌아올 때마다 새로 읽는다

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  late Future<Overview> _data = loadOverview();

  void _reload() => setState(() { _data = loadOverview(); });

  @override
  void didUpdateWidget(HomePage old) {
    super.didUpdateWidget(old);
    if (widget.active && !old.active) _reload();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: topBar('오늘'),
        body: FutureBuilder(
          future: _data,
          builder: (context, snapshot) {
            if (snapshot.hasError) return ErrorRetry(snapshot.error!, _reload);
            if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
            return RefreshIndicator(onRefresh: () async => _reload(), child: _body(snapshot.data!));
          },
        ),
      );

  Widget _body(Overview o) {
    final balance = o.balance;
    return ListView(padding: const EdgeInsets.all(16), children: [
      RingsCard(overview: o, big: true),
      if (balance == null)
        Card(
          child: ListTile(
            title: Text(kIsWeb ? '폰 앱을 열면 잔고가 여기에 보여요' : '증권사를 연결하면 잔고를 볼 수 있어요'),
            trailing: kIsWeb ? null : const Icon(Icons.chevron_right),
            onTap: kIsWeb
                ? null
                : () async {
                    await Navigator.of(context).push(pageRoute(const BrokerPage()));
                    _reload();
                  },
          ),
        )
      else ...[
        Row(children: [
          Expanded(child: _stat('예수금 (결제 전 포함)', won(balance['cash_krw'] as int))),
          const SizedBox(width: 10),
          Expanded(child: _stat('주식 평가금', won(totals(balance).value))),
        ]),
        Padding(padding: const EdgeInsets.only(left: 4, top: 2), child: SourceText(sourceOf(balance))),
        const SizedBox(height: 16),
        const Text('보유 종목', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900)),
        if (holdingsOf(balance).isEmpty) const Padding(padding: EdgeInsets.all(8), child: Text('보유 종목이 없어요')),
        for (final h in holdingsOf(balance)) _holding(h),
      ],
      const SizedBox(height: 16),
      const Text('이렇게 물어보세요', style: TextStyle(fontWeight: FontWeight.bold, color: mutedText)),
      const SizedBox(height: 8),
      Wrap(spacing: 8, runSpacing: 8, children: [
        for (final text in ['잔고 보여줘', '삼성전자 사도 돼?', '아까 주문 체결됐어?'])
          ActionChip(label: Text(text), onPressed: () => widget.onAsk(text)),
      ]),
    ]);
  }

  Widget _stat(String label, String value) => Card(
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(label, style: const TextStyle(fontSize: 12, color: mutedText)),
            FittedBox(fit: BoxFit.scaleDown, child: Text(value, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w900))),
          ]),
        ),
      );

  Widget _holding(Map<String, dynamic> h) {
    final avg = h['avg_price'] as int;
    final qty = h['qty'] as int;
    final price = priceOf(h);
    final gain = (price - avg) * qty;
    final name = h['stock_name'] as String;
    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: RoomAvatar(text: name.length <= 2 ? name : name.substring(0, 2), color: softGray, foreground: ink, size: 44),
      title: Text(name, style: const TextStyle(fontWeight: FontWeight.bold)),
      subtitle: Text('${comma(qty)}주 · 평균 ${won(avg)}'),
      trailing: Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.end, children: [
        Text(won(price * qty), style: const TextStyle(fontWeight: FontWeight.bold)),
        Text('${gain > 0 ? '+' : ''}${comma(gain)}원 (${rateText(gain, avg * qty)})',
            style: TextStyle(fontSize: 12, color: changeColor(gain), fontWeight: FontWeight.bold)),
      ]),
      onTap: () => widget.onAsk('$name 더 사도 돼?'),
    );
  }
}
