// S-05 홈: 계좌 요약, 보유 종목, 승인 대기 건수, 대화 바로가기
// 앱은 증권사(지금은 가짜)에서 직접 읽고 서버에 스냅샷(계좌번호 없음)을 올린다. 웹은 서버 스냅샷을 본다.

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../../api/api.dart';
import '../../broker/fake_broker.dart';
import '../../common/common.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key, required this.onAsk, required this.active});
  final void Function(String text) onAsk;
  final bool active; // 홈 탭으로 돌아올 때마다 새로 읽는다

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  Future<(Map<String, dynamic>, int)>? _data;
  final _input = TextEditingController();

  @override
  void initState() {
    super.initState();
    _data = _load();
  }

  @override
  void didUpdateWidget(HomePage old) {
    super.didUpdateWidget(old);
    if (widget.active && !old.active) setState(() => _data = _load());
  }

  Future<(Map<String, dynamic>, int)> _load() async {
    Map<String, dynamic> balance;
    if (kIsWeb) {
      balance = await api.get('/api/snapshot') as Map<String, dynamic>;
    } else {
      balance = broker.balance();
      await api.post('/api/snapshot', balance);
    }
    final waiting = await api.get('/api/approvals?status=needs_approval') as List;
    return (balance, waiting.length);
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: topBar('홈'),
        body: FutureBuilder(
          future: _data,
          builder: (context, snapshot) {
            if (snapshot.hasError) return ErrorRetry(snapshot.error!, () => setState(() => _data = _load()));
            if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
            final (balance, waitingCount) = snapshot.data!;
            return RefreshIndicator(
              onRefresh: () async => setState(() => _data = _load()),
              child: _body(balance, waitingCount),
            );
          },
        ),
      );

  Widget _body(Map<String, dynamic> balance, int waitingCount) {
    final holdings = (balance['holdings'] as List).cast<Map<String, dynamic>>();
    final cash = balance['cash_krw'] as int;
    int priceOf(Map<String, dynamic> h) => broker.priceOf(h['stock_code'] as String) ?? h['avg_price'] as int;
    final total = cash + holdings.fold<int>(0, (sum, h) => sum + priceOf(h) * (h['qty'] as int));
    final source = kIsWeb ? '폰 동기화 ${hhmm(balance['fetched_at'] as String)} 기준'
        : '$fakeBrokerName(가짜 데이터) · ${hhmm(balance['fetched_at'] as String)} 기준';

    return ListView(padding: const EdgeInsets.all(16), children: [
      Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('총 평가금액'),
            Text(won(total), style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text('현금 ${won(cash)} · 오늘 손익 미확인'),
            SourceText(source),
          ]),
        ),
      ),
      if (waitingCount > 0)
        Card(
          color: Colors.amber.withValues(alpha: 0.15),
          child: ListTile(
            leading: const Icon(Icons.fact_check),
            title: Text('승인 대기 $waitingCount건'),
            subtitle: const Text('승인 대기 탭에서 확인해 주세요'),
          ),
        ),
      const SizedBox(height: 8),
      const Text('보유 종목', style: TextStyle(fontWeight: FontWeight.bold)),
      if (holdings.isEmpty) const Padding(padding: EdgeInsets.all(8), child: Text('보유 종목이 없어요')),
      for (final h in holdings) _holdingTile(h, priceOf(h)),
      const SizedBox(height: 16),
      Wrap(spacing: 8, children: [
        for (final text in ['잔고 보여줘', '삼성전자 사도 돼?', '기아 2주 사줘'])
          ActionChip(label: Text(text), onPressed: () => widget.onAsk(text)),
      ]),
      TextField(
        controller: _input,
        decoration: const InputDecoration(hintText: '무엇이든 물어보세요', suffixIcon: Icon(Icons.send)),
        onSubmitted: (text) {
          if (text.trim().isEmpty) return;
          _input.clear();
          widget.onAsk(text.trim());
        },
      ),
    ]);
  }

  Widget _holdingTile(Map<String, dynamic> h, int price) {
    final avg = h['avg_price'] as int;
    final rate = avg == 0 ? 0.0 : (price - avg) * 100 / avg;
    return ListTile(
      contentPadding: EdgeInsets.zero,
      title: Text(h['stock_name'] as String),
      subtitle: Text('${comma(h['qty'] as int)}주 · 평균 ${won(avg)}'),
      trailing: Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.end, children: [
        Text(won(price)),
        Text('${rate > 0 ? '+' : ''}${rate.toStringAsFixed(1)}%', style: TextStyle(color: changeColor(rate))),
      ]),
    );
  }
}
