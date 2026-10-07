// 모의투자 자동매매 켜기·끄기, 한 번 금액, 오늘 기록 (features/auto/auto_trader.dart)

import 'package:flutter/material.dart';

import '../../broker/broker.dart';
import '../../common/common.dart';
import 'auto_trader.dart';

class AutoTradePage extends StatelessWidget {
  const AutoTradePage({super.key});

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
              Card(
                color: Colors.white,
                child: ListTile(
                  title: const Text('오늘 투자할 총액'),
                  subtitle: const Text('후보 종목에 나눠 사요. 1회·1일 한도는 투자 정책을 따라요'),
                  trailing: DropdownButton<int>(
                    value: autoTrader.budgetKrw,
                    items: [for (final v in const [1000000, 3000000, 5000000]) DropdownMenuItem(value: v, child: Text(won(v)))],
                    onChanged: (v) => autoTrader.setBudgetKrw(v!),
                  ),
                ),
              ),
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 8),
                child: SourceText('장중(평일 09:05~15:00) 앱이 켜져 있으면 1분마다 확인해서 사고, 15:00~15:15에 오늘 자동으로 산 것을 팔아요. 오늘 아침 브리핑에서 투자 AI가 매수 검토로 쓰고 '
                    '검증 AI가 승인한 종목만, 주문 때 다시 투자 AI → 검증 AI → 한도 검사를 거쳐 하루 최대 $autoMaxPerDay종목 사요. '
                    '성향 초과·검증 반려·급등 재확인처럼 확인이 필요한 처리안은 자동으로 승인하지 않아요. 수익을 보장하지 않아요. '
                    '같은 날 사고팔면 수수료와 매도 세금(0.2%)이 들어요.'),
              ),
              Text('오늘 기록', style: TextStyle(fontFamily: displayFont, fontSize: 20)),
              const SizedBox(height: 8),
              if (autoTrader.log.isEmpty) const Text('아직 없어요', style: TextStyle(color: mutedText)),
              for (final line in autoTrader.log.reversed) Padding(padding: const EdgeInsets.only(bottom: 6), child: Text(line)),
            ]);
          },
        ),
      );
}
