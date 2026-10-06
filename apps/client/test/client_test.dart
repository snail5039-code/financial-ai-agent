import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:invest_client/api/api.dart';
import 'package:invest_client/broker/fake_broker.dart';
import 'package:invest_client/common/common.dart';

Map<String, dynamic> order(String side, int qty, int price, {String key = 'k1', int? approved}) => {
      'approval_id': key, 'stock_code': '000270', 'side': side, 'qty': qty, 'limit_price': price,
      'approved_price': approved ?? price, 'max_price_drift_pct': 1, 'idempotency_key': key,
    };

void main() {
  test('금액 표시: 천 단위 콤마, 음수, 반올림', () {
    expect(won(1250000), '1,250,000원');
    expect(comma(999), '999');
    expect(comma(-1000), '-1,000');
    expect(comma(0), '0');
    expect(comma(1234.6), '1,235');
  });

  test('시각은 기기 시간대와 상관없이 한국 시각으로 보여준다', () {
    expect(hhmm('2026-10-06T02:40:00Z'), '11:40');
    expect(hhmm('2026-10-06T11:40:05+09:00'), '11:40');
  });

  test('이벤트 스트림: 빈 줄로 이벤트를 나누고 한글을 그대로 읽는다', () async {
    final lines = Stream.fromIterable([
      'event: progress', 'data: {"step": "understand", "label": "요청 이해 중"}', '',
      'event: done', 'data: {"thread_id": "t1"}', '',
    ]);
    final events = await parseSse(lines).toList();
    expect(events.map((e) => e.event), ['progress', 'done']);
    expect(events.first.data['label'], '요청 이해 중');
  });

  group('가짜 증권사 주문', () {
    test('매수하면 현금이 줄고 평균 단가가 합쳐진다', () {
      final b = FakeBroker()..holdings['000270'] = (qty: 2, avgPrice: 100000);
      final result = b.execute(order('buy', 2, 113300));
      expect(result['status'], 'filled');
      expect(b.cash, 1500000 - 226600);
      expect(b.holdings['000270'], (qty: 4, avgPrice: 106650));
    });

    test('같은 idempotency_key는 한 번만 주문한다', () {
      final b = FakeBroker();
      final first = b.execute(order('buy', 1, 113300));
      final second = b.execute(order('buy', 1, 113300));
      expect(second, same(first));
      expect(b.cash, 1500000 - 113300);
    });

    test('승인 가격에서 1% 넘게 바뀌면 주문하지 않고 지금 가격을 알린다', () {
      final b = FakeBroker();
      final result = b.execute(order('buy', 1, 110000, approved: 110000)); // 지금 113,300 (3% 차이)
      expect(result['status'], 'price_changed');
      expect(result['current_price'], 113300);
      expect(b.cash, 1500000);
    });

    test('현금·보유 수량이 부족하면 실패하고 아무것도 바꾸지 않는다', () {
      final b = FakeBroker();
      expect(b.execute(order('buy', 20, 113300, key: 'a'))['status'], 'failed');
      expect(b.execute(order('sell', 1, 113300, key: 'b'))['status'], 'failed');
      expect(b.cash, 1500000);
      expect(b.holdings.containsKey('000270'), isFalse);
    });

    test('전부 팔면 보유 목록에서 빠지고 현금이 는다', () {
      final b = FakeBroker()..holdings['000270'] = (qty: 2, avgPrice: 100000);
      expect(b.execute(order('sell', 2, 113300))['status'], 'filled');
      expect(b.holdings.containsKey('000270'), isFalse);
      expect(b.cash, 1500000 + 226600);
    });

    test('조회: 없는 종목이면 가짜 값 없이 실패로 답한다', () {
      final b = FakeBroker();
      expect(b.answerFetch([{'type': 'price', 'stock_code': '999999'}]).keys, ['error']);
      final ok = b.answerFetch([{'type': 'balance'}, {'type': 'price', 'stock_code': '005930'}]);
      expect((ok['balance'] as Map)['cash_krw'], 1500000);
      expect((ok['prices'] as List).single['price'], 276000);
      expect(((ok['balance'] as Map)['fetched_at'] as String).endsWith('Z'), isTrue); // 서버는 시간대 있는 시각만 받는다
    });
  });
}
