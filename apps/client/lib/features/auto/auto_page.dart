// 모의투자 자동매매 켜기·끄기, 오늘 계획 승인(살 총액·팔 종목), 오늘 기록 (features/auto/auto_trader.dart)

import 'package:flutter/material.dart';

import '../../broker/broker.dart';
import '../../common/common.dart';
import 'auto_trader.dart';

class AutoTradePage extends StatefulWidget {
  const AutoTradePage({super.key});

  @override
  State<AutoTradePage> createState() => _AutoTradePageState();
}

class _AutoTradePageState extends State<AutoTradePage> {
  int? _budget; // 승인 전 고르는 중인 값 (null이면 지난번 값)
  Set<String>? _sell; // 승인 전 고르는 중인 팔 종목 (null이면 자동매매로 산 것 전부)
  bool _aiSell = true; // 장중 급락 시 AI 판단 매도 허용

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: topBar('모의 자동매매'),
        body: ListenableBuilder(
          listenable: Listenable.merge([autoTrader, currentBroker]),
          builder: (context, _) {
            final allowed = AutoTrader.allowed(currentBroker.value);
            return ListView(padding: const EdgeInsets.all(16), children: [
              Card(
                color: Colors.white,
                child: SwitchListTile(
                  title: const Text('자동매매', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 18)),
                  subtitle: Text(allowed ? '모의투자에서만 동작해요. 끄면 바로 멈춰요' : '모의투자(KIS 모의) 연결에서만 켤 수 있어요'),
                  value: autoTrader.on && allowed,
                  onChanged: allowed ? autoTrader.setOn : null,
                ),
              ),
              if (autoTrader.on && allowed) _planCard(),
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 8),
                child: SourceText('매일 오늘 계획(살 총액, 팔 종목)을 승인해야 시작해요. 승인하지 않은 날은 사고팔지 않아요. '
                    '장중(평일 09:05~15:00) 앱이 켜져 있으면 1분마다 확인해서 오늘 아침 브리핑에서 검증 AI가 승인한 종목을 사고, '
                    '15:00~15:28에 고른 종목을 팔아요. 허용하면 장중에 자동매매로 산 종목이 매입가보다 $autoDropPct% 넘게 내릴 때 '
                    'AI가 매도를 제안하고 검증 AI가 승인한 경우에만 팔아요. 사든 팔든 주문 때 다시 투자 AI → 검증 AI → 한도 검사를 거치고, 1회 한도를 넘으면 나눠 주문해요. '
                    '성향 초과·검증 반려·급등 재확인처럼 확인이 필요한 처리안은 자동으로 승인하지 않아요. 수익을 보장하지 않아요. '
                    '사고팔 때마다 수수료, 팔 때 세금(0.2%)이 들어요.'),
              ),
              Text('오늘 기록', style: TextStyle(fontFamily: displayFont, fontSize: 20)),
              const SizedBox(height: 8),
              if (autoTrader.log.isEmpty) const Text('아직 없어요', style: TextStyle(color: mutedText)),
              for (final line in autoTrader.log.reversed) Padding(padding: const EdgeInsets.only(bottom: 6), child: Text(line)),
            ]);
          },
        ),
      );

  Widget _planCard() {
    final plan = autoTrader.plan;
    final held = autoTrader.positions;
    String nameOf(String code) => (held[code] as Map?)?['name'] as String? ?? code;
    if (plan != null) {
      final sell = (plan['sell'] as List).cast<String>();
      return Card(
        color: Colors.white,
        child: ListTile(
          title: const Text('오늘 계획 (승인함)', style: TextStyle(fontWeight: FontWeight.w700)),
          subtitle: Text('매수: ${plan['budget'] == 0 ? '안 함' : '${won(plan['budget'] as int)}까지'}\n'
              '매도(15:00 이후): ${sell.isEmpty ? '안 함' : sell.map(nameOf).join(', ')}\n'
              '장중 급락 시 AI 판단 매도: ${plan['ai_sell'] == true ? '허용' : '안 함'}'),
          isThreeLine: true,
          trailing: TextButton(onPressed: autoTrader.cancelPlan, child: const Text('계획 취소')),
        ),
      );
    }
    final budget = _budget ?? autoTrader.budgetKrw;
    final sell = _sell ?? held.keys.toSet();
    return Card(
      color: const Color(0xFFFFF4E0),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('오늘 계획을 승인해 주세요', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 16)),
          const Text('승인하기 전에는 사지도 팔지도 않아요'),
          const SizedBox(height: 8),
          Row(children: [
            const Expanded(child: Text('오늘 살 총액')),
            DropdownButton<int>(
              value: AutoTrader.budgets.contains(budget) ? budget : AutoTrader.budgets[1],
              items: [for (final v in AutoTrader.budgets) DropdownMenuItem(value: v, child: Text(v == 0 ? '사지 않음' : won(v)))],
              onChanged: (v) => setState(() => _budget = v),
            ),
          ]),
          const SizedBox(height: 4),
          Text(held.isEmpty ? '팔 종목: 자동매매로 산 종목이 없어요' : '15:00 이후 팔 종목 (자동매매로 산 것)'),
          for (final e in held.entries)
            CheckboxListTile(
              dense: true,
              contentPadding: EdgeInsets.zero,
              value: sell.contains(e.key),
              title: Text('${(e.value as Map)['name']} ${(e.value as Map)['qty']}주'),
              onChanged: (v) => setState(() => _sell = {...sell}..remove(e.key)..addAll(v! ? [e.key] : [])),
            ),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            value: _aiSell,
            title: const Text('장중 급락 시 AI 판단으로 매도'),
            subtitle: const Text('자동매매로 산 종목이 매입가보다 $autoDropPct% 넘게 내리면 투자 AI·검증 AI가 팔지 판단해요'),
            onChanged: (v) => setState(() => _aiSell = v),
          ),
          const SizedBox(height: 8),
          FilledButton(
            onPressed: () => autoTrader.approvePlan(budget, sell.toList(), aiSell: _aiSell),
            child: const Text('오늘 계획 승인'),
          ),
        ]),
      ),
    );
  }
}
