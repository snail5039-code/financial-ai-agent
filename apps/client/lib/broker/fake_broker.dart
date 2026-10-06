// 6단계용 가짜 증권사. 서버의 fetch(잔고·현재가)와 execute(주문) 멈춤에 답한다.
// 7단계에서 KIS 모의투자 어댑터로 바꾼다. 화면에는 항상 "가짜 데이터"로 표시한다.
// 가격은 2026-10-01 실제 종가(금융위원회_주식시세정보)를 고정값으로 쓴다. 실시간 가격이 아니다.

const fakeBrokerName = '가짜 증권사';

const _prices = <String, (String, int)>{
  '000270': ('기아', 113300),
  '000660': ('SK하이닉스', 1833000),
  '000810': ('삼성화재', 626000),
  '005380': ('현대차', 349000),
  '005490': ('POSCO홀딩스', 306500),
  '005930': ('삼성전자', 276000),
  '006400': ('삼성SDI', 517000),
  '009150': ('삼성전기', 1561000),
  '010120': ('LS ELECTRIC', 206000),
  '012330': ('현대모비스', 382000),
  '012450': ('한화에어로스페이스', 1034000),
  '028260': ('삼성물산', 347000),
  '032830': ('삼성생명', 284000),
  '034020': ('두산에너빌리티', 82100),
  '034730': ('SK', 587000),
  '035420': ('NAVER', 191200),
  '042660': ('한화오션', 78500),
  '042700': ('한미반도체', 268500),
  '055550': ('신한지주', 103800),
  '066570': ('LG전자', 211500),
  '068270': ('셀트리온', 183600),
  '086790': ('하나금융지주', 128300),
  '105560': ('KB금융', 166000),
  '207940': ('삼성바이오로직스', 1429000),
  '267260': ('HD현대일렉트릭', 673000),
  '298040': ('효성중공업', 2822000),
  '316140': ('우리금융지주', 33250),
  '329180': ('HD현대중공업', 431500),
  '373220': ('LG에너지솔루션', 360500),
  '402340': ('SK스퀘어', 1155000),
};

String _nowIso() => DateTime.now().toUtc().toIso8601String();

class FakeBroker {
  int cash = 1500000;
  // 종목코드 → 수량·평균 매입가
  final holdings = <String, ({int qty, int avgPrice})>{'005930': (qty: 3, avgPrice: 240000)};
  // 같은 주문(idempotency_key)을 두 번 실행하지 않게 결과를 기억한다
  final _results = <String, Map<String, dynamic>>{};

  String nameOf(String code) => _prices[code]?.$1 ?? code;
  int? priceOf(String code) => _prices[code]?.$2;

  /// 서버로 보내는 잔고 형식 (계좌번호 없음)
  Map<String, dynamic> balance() => {
        'cash_krw': cash,
        'holdings': [
          for (final e in holdings.entries)
            {'stock_code': e.key, 'stock_name': nameOf(e.key), 'qty': e.value.qty, 'avg_price': e.value.avgPrice},
        ],
        'fetched_at': _nowIso(),
      };

  /// fetch 멈춤의 답. 하나라도 조회 못 하면 가짜 값 없이 실패로 답한다
  Map<String, dynamic> answerFetch(List<dynamic> needs) {
    final answer = <String, dynamic>{};
    for (final need in needs.cast<Map<String, dynamic>>()) {
      if (need['type'] == 'balance') answer['balance'] = balance();
      if (need['type'] == 'price') {
        final code = need['stock_code'] as String;
        final price = priceOf(code);
        if (price == null) return {'error': '$fakeBrokerName에 없는 종목이에요 ($code)'};
        (answer['prices'] ??= <Map<String, dynamic>>[]).add({'stock_code': code, 'price': price, 'as_of': _nowIso()});
      }
    }
    return answer;
  }

  /// execute 멈춤의 답: 가격 재확인 → 주문 → 결과 (생체인증은 7단계에서 넣는다)
  Map<String, dynamic> execute(Map<String, dynamic> request) {
    final key = request['idempotency_key'] as String;
    return _results[key] ??= _execute(request, key);
  }

  Map<String, dynamic> _execute(Map<String, dynamic> request, String key) {
    final code = request['stock_code'] as String;
    final qty = request['qty'] as int;
    final limitPrice = request['limit_price'] as int;
    final approvedPrice = request['approved_price'] as int;
    Map<String, dynamic> failed(String message) => {'idempotency_key': key, 'status': 'failed', 'message': message};

    final current = priceOf(code);
    if (current == null) return failed('$fakeBrokerName에 없는 종목이에요');
    final driftPct = (current - approvedPrice).abs() * 100 / approvedPrice;
    if (driftPct > (request['max_price_drift_pct'] as num)) {
      return {'idempotency_key': key, 'status': 'price_changed', 'current_price': current};
    }

    final amount = qty * limitPrice;
    final held = holdings[code];
    if (request['side'] == 'buy') {
      if (amount > cash) return failed('현금이 부족해요');
      cash -= amount;
      final oldQty = held?.qty ?? 0;
      final avg = ((oldQty * (held?.avgPrice ?? 0)) + amount) ~/ (oldQty + qty);
      holdings[code] = (qty: oldQty + qty, avgPrice: avg);
    } else {
      if (held == null || held.qty < qty) return failed('보유 수량이 부족해요');
      cash += amount;
      if (held.qty == qty) {
        holdings.remove(code);
      } else {
        holdings[code] = (qty: held.qty - qty, avgPrice: held.avgPrice);
      }
    }
    return {
      'idempotency_key': key,
      'status': 'filled',
      'broker_order_no': 'FAKE-${DateTime.now().millisecondsSinceEpoch}',
      'filled_qty': qty,
      'filled_price': limitPrice,
      'message': '가짜 체결 (6단계 테스트용, 실제 주문 아님)',
    };
  }
}

final broker = FakeBroker();
