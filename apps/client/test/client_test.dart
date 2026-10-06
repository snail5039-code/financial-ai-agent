import 'dart:async';
import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:invest_client/api/api.dart';
import 'package:invest_client/broker/broker.dart';
import 'package:invest_client/broker/fake_broker.dart';
import 'package:invest_client/broker/kis_mock_broker.dart';
import 'package:invest_client/common/common.dart';
import 'package:invest_client/features/history/history_page.dart';
import 'package:invest_client/secure/key_store.dart';

Map<String, dynamic> order(String side, int qty, int price, {String key = 'k1', int? approved}) => {
      'approval_id': key, 'stock_code': '000270', 'side': side, 'qty': qty, 'limit_price': price,
      'approved_price': approved ?? price, 'max_price_drift_pct': 1, 'idempotency_key': key,
    };

http.Response jsonResponse(Object body) =>
    http.Response.bytes(utf8.encode(jsonEncode(body)), 200, headers: {'content-type': 'application/json'});

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

  test('기록: 최종 결과와 검증 항목 이름', () {
    expect(finalResult({'order_status': 'filled', 'approval_status': 'approved'}), '체결');
    expect(finalResult({'approval_status': 'rejected'}), '거절');
    expect(finalResult({'policy_ok': false}), '정책 차단');
    expect(finalResult({'policy_ok': null}), '분석');
    expect(checkTarget('claim:0'), '근거 1');
    expect(checkTarget('freshness'), '자료 시점');
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

  group('주문 실행 (가짜 증권사)', () {
    late FakeBroker b;
    late OrderJournal journal;
    var unlocked = 0;
    Future<bool> unlock() async {
      unlocked++;
      return true;
    }

    Future<Map<String, dynamic>> run(Map<String, dynamic> request) =>
        executeOrder(b, request, unlock: unlock, journal: journal);

    setUp(() {
      b = FakeBroker();
      journal = OrderJournal(SecureBox.memory());
      unlocked = 0;
    });

    test('매수하면 현금이 줄고 평균 단가가 합쳐진다', () async {
      b.holdings['000270'] = (qty: 2, avgPrice: 100000);
      final result = await run(order('buy', 2, 113300));
      expect(result['status'], 'filled');
      expect(b.cash, 1500000 - 226600);
      expect(b.holdings['000270'], (qty: 4, avgPrice: 106650));
      expect(unlocked, 0); // 가짜 증권사는 폰 잠금 확인을 건너뛴다
    });

    test('같은 idempotency_key는 한 번만 주문한다', () async {
      final first = await run(order('buy', 1, 113300));
      final second = await run(order('buy', 1, 113300));
      expect(second, first);
      expect(b.cash, 1500000 - 113300);
    });

    test('승인 가격에서 1% 넘게 바뀌면 주문하지 않고 지금 가격을 알린다', () async {
      final result = await run(order('buy', 1, 110000)); // 지금 113,300 (3% 차이)
      expect(result['status'], 'price_changed');
      expect(result['current_price'], 113300);
      expect(b.cash, 1500000);
      // 같은 처리안으로 다시 승인하면 같은 key로 다시 실행할 수 있어야 한다
      expect((await run(order('buy', 1, 113300)))['status'], 'filled');
    });

    test('현금·보유 수량이 부족하면 실패하고 아무것도 바꾸지 않는다', () async {
      expect((await run(order('buy', 20, 113300, key: 'a')))['status'], 'failed');
      expect((await run(order('sell', 1, 113300, key: 'b')))['status'], 'failed');
      expect(b.cash, 1500000);
      expect(b.holdings.containsKey('000270'), isFalse);
    });

    test('주문을 보낸 뒤 앱이 꺼졌으면 다시 주문하지 않고 주문 내역으로 확인한다', () async {
      await journal.start('k1', '000000');
      await b.order('buy', '000270', 1, 113300); // 지난번에 실제로 들어간 주문
      final result = await run(order('buy', 1, 113300));
      expect(result['status'], 'unknown_checked');
      expect(result['broker_order_no'], startsWith('FAKE-'));
      expect(b.holdings['000270']!.qty, 1); // 두 번 사지 않았다
    });

    test('증권사가 없으면 주문하지 않는다', () async {
      final result = await executeOrder(null, order('buy', 1, 113300), unlock: unlock, journal: journal);
      expect(result['status'], 'failed');
    });

    test('조회: 없는 종목이면 가짜 값 없이 실패로 답한다', () async {
      expect((await answerFetch(b, [{'type': 'price', 'stock_code': '999999'}])).keys, ['error']);
      expect((await answerFetch(null, [{'type': 'balance'}])).keys, ['error']);
      final ok = await answerFetch(b, [{'type': 'balance'}, {'type': 'price', 'stock_code': '005930'}]);
      expect((ok['balance'] as Map)['cash_krw'], 1500000);
      expect((ok['prices'] as List).single['price'], 276000);
      expect(((ok['balance'] as Map)['fetched_at'] as String).endsWith('Z'), isTrue); // 서버는 시간대 있는 시각만 받는다
    });
  });

  group('KIS 모의투자 (가짜 응답)', () {
    final keys = BrokerKeys(appKey: 'test-app-key', appSecret: 'test-secret', account: '12345678-01');
    late List<http.Request> sent;

    KisMockBroker kis(Future<http.Response> Function(http.Request) handler) {
      sent = [];
      return KisMockBroker(keys, box: SecureBox.memory(), client: MockClient((request) {
        sent.add(request);
        if (request.url.path == '/oauth2/tokenP') {
          return Future.value(jsonResponse({'access_token': 'tok', 'access_token_token_expired': '2099-01-01 00:00:00'}));
        }
        return handler(request);
      }));
    }

    test('모의투자 서버와 모의 거래 코드만 쓰고, 주문 형식이 맞다', () async {
      final b = kis((_) async => jsonResponse({'rt_cd': '0', 'msg1': '주문 전송 완료', 'output': {'ODNO': '0000117057'}}));
      final ack = await b.order('buy', '000270', 2, 113300);
      expect(ack.orderNo, '0000117057');
      final body = jsonDecode(sent.last.body) as Map<String, dynamic>;
      expect(sent.last.headers['tr_id'], 'VTTC0012U');
      expect(sent.last.headers['authorization'], 'Bearer tok');
      expect(body, containsPair('CANO', '12345678'));
      expect(body, containsPair('ACNT_PRDT_CD', '01'));
      expect(body, containsPair('ORD_DVSN', '00')); // 지정가
      expect(body, containsPair('ORD_UNPR', '113300'));
      await b.order('sell', '000270', 1, 113300);
      expect(sent.last.headers['tr_id'], 'VTTC0011U');
      for (final r in sent) {
        expect(r.url.host, 'openapivts.koreainvestment.com');
        expect(r.headers['tr_id'] ?? 'V', isNot(startsWith('T'))); // 실전 거래 코드(T…)는 없다
      }
      expect(sent.where((r) => r.url.path == '/oauth2/tokenP').length, 1); // 토큰은 한 번만 받는다
    });

    test('rt_cd가 0이 아니면 거절(BrokerError)이다', () async {
      final b = kis((_) async => jsonResponse({'rt_cd': '1', 'msg1': '모의투자 주문가능금액을 초과 했습니다'}));
      await expectLater(b.order('buy', '000270', 999, 113300), throwsA(isA<BrokerError>()));
    });

    test('잔고: 계좌번호 없이 서버 형식으로 바꾼다', () async {
      final b = kis((_) async => jsonResponse({
            'rt_cd': '0',
            'output1': [
              {'pdno': '005930', 'prdt_name': '삼성전자', 'hldg_qty': '3', 'pchs_avg_pric': '240000.0000', 'prpr': '276000'},
              {'pdno': '000270', 'prdt_name': '기아', 'hldg_qty': '0', 'pchs_avg_pric': '0', 'prpr': '113300'},
            ],
            'output2': [{'dnca_tot_amt': '9172000'}],
          }));
      final balance = await b.balance();
      expect(balance['cash_krw'], 9172000);
      expect(balance['holdings'], [{'stock_code': '005930', 'stock_name': '삼성전자', 'qty': 3, 'avg_price': 240000}]);
      expect(b.lastPrices['005930'], 276000);
      expect(sent.last.headers['tr_id'], 'VTTC8434R');
      expect(jsonEncode(balance), isNot(contains('12345678'))); // 서버로 가는 값에 계좌번호가 없다
    });

    test('주문 응답이 없으면 다시 주문하지 않고 주문 내역에서 찾는다', () async {
      var orders = 0;
      final b = kis((request) async {
        if (request.url.path.endsWith('order-cash')) {
          orders++;
          throw TimeoutException('응답 없음');
        }
        if (request.url.path.endsWith('inquire-price')) {
          return jsonResponse({'rt_cd': '0', 'output': {'stck_prpr': '113300'}});
        }
        return jsonResponse({'rt_cd': '0', 'output1': [
          {'odno': '0000117057', 'sll_buy_dvsn_cd': '02', 'ord_qty': '2', 'ord_unpr': '113300',
           'tot_ccld_qty': '2', 'avg_prvs': '113300', 'ord_tmd': '235959'},
        ]});
      });
      final journal = OrderJournal(SecureBox.memory());
      var unlocked = false;
      final result = await executeOrder(b, order('buy', 2, 113300), journal: journal, unlock: () async => unlocked = true);
      expect(unlocked, isTrue); // 실제 증권사는 폰 잠금 확인을 한다
      expect(orders, 1);
      expect(result['status'], 'unknown_checked');
      expect(result['broker_order_no'], '0000117057');
      expect(sent.last.headers['tr_id'], 'VTTC0081R');
      // 같은 주문을 다시 실행해도 증권사에 다시 보내지 않는다
      expect(await executeOrder(b, order('buy', 2, 113300), journal: journal, unlock: () async => true), result);
      expect(orders, 1);
    });

    test('폰 잠금 확인을 안 하면 주문하지 않는다', () async {
      final b = kis((request) async => jsonResponse({'rt_cd': '0', 'output': {'stck_prpr': '113300'}}));
      final result = await executeOrder(b, order('buy', 1, 113300),
          journal: OrderJournal(SecureBox.memory()), unlock: () async => false);
      expect(result['status'], 'failed');
      expect(sent.where((r) => r.url.path.endsWith('order-cash')), isEmpty);
    });

    test('계좌번호 형식이 틀리면 저장하지 않는다', () {
      expect(() => BrokerKeys(appKey: 'a', appSecret: 'b', account: '1234'), throwsFormatException);
    });
  });
}
