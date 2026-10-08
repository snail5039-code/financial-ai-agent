// 한국투자증권(KIS) 모의투자 어댑터 (FR-06c). 주문 흐름 개발·검증용이다.
// 모의투자 서버 주소와 모의 거래 코드(V로 시작)만 쓴다. 실전 주소·실전 거래 코드는 이 파일에 넣지 않는다 (AGENTS.md 4장).
// API: https://apiportal.koreainvestment.com, 예시 코드 https://github.com/koreainvestment/open-trading-api

import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../secure/key_store.dart';
import 'broker.dart';

const kisMockBaseUrl = 'https://openapivts.koreainvestment.com:29443';
const _timeout = Duration(seconds: 30); // 모의투자 잔고 조회가 10초를 넘길 때가 있었다 (2026-10-08 장중)
// 모의투자는 초당 호출 수가 적다 ("초당 거래건수를 초과" 오류). 호출 시작 사이를 이만큼 띄운다.
// 550ms로는 채팅 목록 읽기와 대화 조회가 겹칠 때 걸렸다 (2026-10-07). tools/kis_mock_check.py도 1.1초 간격
const _minGap = Duration(milliseconds: 1000);
const _rateLimitRetries = 3;

class KisMockBroker implements Broker {
  KisMockBroker(this.keys, {http.Client? client, SecureBox? box})
      : _http = client ?? http.Client(),
        _box = box ?? secureBox;

  final BrokerKeys keys;
  final http.Client _http;
  final SecureBox _box;
  String? _token;
  DateTime? _tokenExpires;
  Future<void> _lastCall = Future.value();

  /// 마지막 잔고 조회에서 받은 현재가 (홈 화면 평가금액용)
  @override
  final lastPrices = <String, int>{};

  @override
  String get name => 'KIS 모의투자';
  @override
  bool get isFake => false;

  // ---------- 접속 토큰 ----------
  // 토큰은 하루 동안 쓸 수 있고 발급은 1분에 한 번만 된다. 그래서 폰 보안 저장소에 두고 다시 쓴다

  Future<String> _accessToken() async {
    final now = DateTime.now();
    if (_token == null) {
      _token = await _box.read('kis_token');
      final expires = await _box.read('kis_token_expires');
      _tokenExpires = expires == null ? null : DateTime.parse(expires);
    }
    if (_token != null && _tokenExpires != null && now.isBefore(_tokenExpires!)) return _token!;

    final data = await _send(http.Request('POST', Uri.parse('$kisMockBaseUrl/oauth2/tokenP'))
      ..headers['content-type'] = 'application/json; charset=utf-8'
      ..body = jsonEncode({'grant_type': 'client_credentials', 'appkey': keys.appKey, 'appsecret': keys.appSecret}));
    final token = data['access_token'];
    if (token is! String) throw BrokerError('KIS 접속 토큰을 받지 못했어요. 앱키·시크리트를 확인해 주세요');
    // 만료 시각은 한국 시각 "2026-10-07 10:32:05". 5분 일찍 새로 받는다
    final expiresKst = DateTime.tryParse('${data['access_token_token_expired']}'.replaceFirst(' ', 'T'));
    _token = token;
    _tokenExpires = expiresKst == null
        ? now.add(const Duration(hours: 23))
        : DateTime.utc(expiresKst.year, expiresKst.month, expiresKst.day, expiresKst.hour - 9, expiresKst.minute)
            .subtract(const Duration(minutes: 5));
    await _box.write('kis_token', token);
    await _box.write('kis_token_expires', _tokenExpires!.toIso8601String());
    return token;
  }

  // ---------- 요청 ----------

  Future<Map<String, dynamic>> _send(http.Request request) async {
    final response = await http.Response.fromStream(await _http.send(request).timeout(_timeout)).timeout(_timeout);
    final Object? data;
    try {
      data = jsonDecode(utf8.decode(response.bodyBytes));
    } on FormatException {
      throw BrokerError('KIS 응답을 읽지 못했어요 (${response.statusCode})');
    }
    if (data is! Map<String, dynamic>) throw BrokerError('KIS 응답 형식이 달라요');
    if (response.statusCode != 200) {
      throw BrokerError('KIS 오류: ${data['msg1'] ?? data['error_description'] ?? response.statusCode}');
    }
    // 거래 API는 HTTP 200이어도 rt_cd가 "0"이 아니면 실패다
    if (data.containsKey('rt_cd') && data['rt_cd'] != '0') {
      throw BrokerError('KIS: ${data['msg1'] ?? data['msg_cd']}'.trim());
    }
    return data;
  }

  Future<Map<String, dynamic>> _call(String method, String path, String trId,
      {Map<String, String>? query, Map<String, String>? body}) async {
    final token = await _accessToken();
    for (var attempt = 1;; attempt++) {
      // 앞 호출이 끝난 뒤 _minGap만큼 기다렸다 보낸다 (동시에 불려도 차례로)
      final previous = _lastCall;
      final turn = Completer<void>();
      _lastCall = turn.future;
      await previous;
      Future.delayed(_minGap, turn.complete);
      final request = http.Request(method, Uri.parse('$kisMockBaseUrl$path').replace(queryParameters: query))
        ..headers.addAll({
          'content-type': 'application/json; charset=utf-8',
          'authorization': 'Bearer $token',
          'appkey': keys.appKey,
          'appsecret': keys.appSecret,
          'tr_id': trId,
          'custtype': 'P',
        });
      if (body != null) request.body = jsonEncode(body);
      try {
        return await _send(request);
      } on BrokerError catch (error) {
        // 초당 호출 제한은 KIS가 요청을 처리하지 않고 돌려보낸 것이라 잠시 뒤 다시 보내도 안전하다 (주문 포함, 2026-10-08)
        if (attempt >= _rateLimitRetries || !error.message.contains('초당 거래건수')) rethrow;
        await Future.delayed(_minGap * 2);
      }
    }
  }

  static int _int(Object? value) => double.tryParse('${value ?? ''}')?.round() ?? 0;

  // ---------- 조회 ----------

  @override
  Future<Map<String, dynamic>> balance() async {
    // ponytail: 첫 페이지(모의 최대 50종목)만 읽는다. 보유 종목이 더 많아지면 CTX_AREA_NK100으로 이어 읽는다
    final data = await _call('GET', '/uapi/domestic-stock/v1/trading/inquire-balance', 'VTTC8434R', query: {
      'CANO': keys.cano, 'ACNT_PRDT_CD': keys.productCode, 'AFHR_FLPR_YN': 'N', 'OFL_YN': '', 'INQR_DVSN': '02',
      'UNPR_DVSN': '01', 'FUND_STTL_ICLD_YN': 'N', 'FNCG_AMT_AUTO_RDPT_YN': 'N', 'PRCS_DVSN': '00',
      'CTX_AREA_FK100': '', 'CTX_AREA_NK100': '',
    });
    final rows = (data['output1'] as List? ?? []).cast<Map<String, dynamic>>().where((r) => _int(r['hldg_qty']) > 0);
    final summary = (data['output2'] as List? ?? [{}]).cast<Map<String, dynamic>>().firstOrNull ?? {};
    for (final r in rows) {
      lastPrices['${r['pdno']}'] = _int(r['prpr']);
    }
    return {
      'cash_krw': _int(summary['dnca_tot_amt']), // 예수금 총액
      'holdings': [
        for (final r in rows)
          {'stock_code': '${r['pdno']}', 'stock_name': '${r['prdt_name']}', 'qty': _int(r['hldg_qty']),
           'avg_price': _int(r['pchs_avg_pric'])},
      ],
      'fetched_at': nowIso(),
    };
  }

  @override
  Future<int> price(String stockCode) async {
    final data = await _call('GET', '/uapi/domestic-stock/v1/quotations/inquire-price', 'FHKST01010100',
        query: {'FID_COND_MRKT_DIV_CODE': 'J', 'FID_INPUT_ISCD': stockCode});
    final price = _int((data['output'] as Map?)?['stck_prpr']);
    if (price <= 0) throw BrokerError('현재가를 받지 못했어요 ($stockCode)');
    return price;
  }

  /// 주식당일분봉조회 (FHKST03010200, 실전·모의 같은 거래 코드). 지금 시각부터 1분봉 30개, 당일만
  @override
  Future<Map<String, dynamic>?> intraday(String stockCode) async {
    final data = await _call('GET', '/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice', 'FHKST03010200', query: {
      'FID_ETC_CLS_CODE': '', 'FID_COND_MRKT_DIV_CODE': 'J', 'FID_INPUT_ISCD': stockCode,
      'FID_INPUT_HOUR_1': kstHhmmss(DateTime.now()), 'FID_PW_DATA_INCU_YN': 'N',
    });
    final bars = [
      for (final b in ((data['output2'] as List?) ?? []).cast<Map<String, dynamic>>())
        if (_int(b['stck_prpr']) > 0) ['${b['stck_cntg_hour']}', _int(b['stck_prpr'])],
    ].reversed.toList(); // KIS는 최신부터 준다
    if (bars.isEmpty) return null; // 장 시작 전
    return {'change_pct': double.tryParse('${(data['output1'] as Map?)?['prdy_ctrt']}'), 'bars': bars};
  }

  // ---------- 주문 ----------

  @override
  Future<({String orderNo, int filledQty, int? filledPrice})> order(String side, String stockCode, int qty, int price) async {
    final data = await _call('POST', '/uapi/domestic-stock/v1/trading/order-cash',
        side == 'buy' ? 'VTTC0012U' : 'VTTC0011U', // 모의 매수 / 모의 매도
        body: {
          'CANO': keys.cano, 'ACNT_PRDT_CD': keys.productCode, 'PDNO': stockCode,
          'ORD_DVSN': '00', // 지정가
          'ORD_QTY': '$qty', 'ORD_UNPR': '$price', 'EXCG_ID_DVSN_CD': 'KRX',
          'SLL_TYPE': side == 'sell' ? '01' : '', 'CNDT_PRIC': '',
        });
    final orderNo = (data['output'] as Map?)?['ODNO'];
    if (orderNo == null) throw BrokerError('KIS가 주문번호를 주지 않았어요');
    // 접수 응답에는 체결 정보가 없다. 체결 여부는 주문 내역에서 본다
    return (orderNo: '$orderNo', filledQty: 0, filledPrice: null);
  }

  @override
  Future<int> buyingPower() async {
    // 매수가능조회는 종목을 받지만 주문가능현금(ord_psbl_cash)은 종목과 상관없다. 시장가(01) 기준으로 묻는다
    final data = await _call('GET', '/uapi/domestic-stock/v1/trading/inquire-psbl-order', 'VTTC8908R', query: {
      'CANO': keys.cano, 'ACNT_PRDT_CD': keys.productCode, 'PDNO': '005930', 'ORD_UNPR': '', 'ORD_DVSN': '01',
      'CMA_EVLU_AMT_ICLD_YN': 'N', 'OVRS_ICLD_YN': 'N',
    });
    return _int((data['output'] as Map?)?['ord_psbl_cash']);
  }

  @override
  Future<List<BrokerOrder>> todayOrders(String stockCode) async {
    final kst = DateTime.now().toUtc().add(const Duration(hours: 9));
    final today = '${kst.year}${kst.month.toString().padLeft(2, '0')}${kst.day.toString().padLeft(2, '0')}';
    // 모의는 한 번에 15건. 종목으로 걸러서 오늘 것만 받는다
    final data = await _call('GET', '/uapi/domestic-stock/v1/trading/inquire-daily-ccld', 'VTTC0081R', query: {
      'CANO': keys.cano, 'ACNT_PRDT_CD': keys.productCode, 'INQR_STRT_DT': today, 'INQR_END_DT': today,
      'SLL_BUY_DVSN_CD': '00', 'PDNO': stockCode, 'CCLD_DVSN': '00', 'INQR_DVSN': '00', 'INQR_DVSN_1': '',
      'INQR_DVSN_3': '00', 'ORD_GNO_BRNO': '', 'ODNO': '', 'EXCG_ID_DVSN_CD': 'KRX',
      'CTX_AREA_FK100': '', 'CTX_AREA_NK100': '',
    });
    return [
      for (final r in (data['output1'] as List? ?? []).cast<Map<String, dynamic>>())
        (
          orderNo: '${r['odno']}',
          stockCode: '${r['pdno']}',
          stockName: '${r['prdt_name']}',
          side: r['sll_buy_dvsn_cd'] == '01' ? 'sell' : 'buy',
          qty: _int(r['ord_qty']),
          price: _int(r['ord_unpr']),
          filledQty: _int(r['tot_ccld_qty']),
          filledPrice: _int(r['avg_prvs']) > 0 ? _int(r['avg_prvs']) : null,
          time: '${r['ord_tmd']}',
        ),
    ];
  }
}
