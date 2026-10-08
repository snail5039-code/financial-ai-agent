// KB증권 Open API 어댑터 (docs/plan/12-todo-by-stage.md 1-7). 조회만 한다. 주문 API는 부르지 않는다 (AGENTS.md 4장).
// 명세: KB 공식 예제 https://github.com/kbsecurities/kb-openapi (example/python, samples.generated.json), 2026-10-07 확인
//   토큰  POST /oauth2/token  {dataHeader: {ipAddr, macAddr}, dataBody: {appKey, appSecret, grantType}} → dataBody.access_token
//   조회  POST /api/v1/{tr}   헤더 appKey, Authorization: bearer <토큰>, 본문 {dataHeader, dataBody: 조회조건}
//   현재가 IVU10140 (주식현재가) dataBody {excg_clsf: 1(KRX), shrt_cd: 종목코드} → now_prc
// 미확인: 잔고·보유 종목·주문 가능 금액·주문 내역 TR (공개 예제에 "고객계좌" 카테고리가 없음),
//        응답 실패 코드 형식, 토큰 유효 시간(expires_in이 없으면 12시간으로 본다). 실제 키로 아직 호출해 보지 않았다.

import 'dart:convert';

import 'package:http/http.dart' as http;

import '../secure/key_store.dart';
import 'broker.dart';

const kbBaseUrl = 'https://developer.kbsec.com:32484';
const _timeout = Duration(seconds: 10);
const _dataHeader = {'ipAddr': '', 'macAddr': ''}; // 폰에서 부를 때는 비워 보내도 된다 (예제 설명)
const _accountNotReady = 'KB 잔고 조회는 아직 준비 중이에요 (KB가 계좌 조회 명세를 공개하면 붙여요)';

class KbBroker implements Broker {
  KbBroker(this.keys, {http.Client? client, SecureBox? box})
      : _http = client ?? http.Client(),
        _box = box ?? secureBox;

  final BrokerKeys keys;
  final http.Client _http;
  final SecureBox _box;
  String? _token;
  DateTime? _tokenExpires;

  @override
  final lastPrices = <String, int>{};

  @override
  String get name => 'KB증권';
  @override
  bool get isFake => false;

  Future<String> _accessToken() async {
    final now = DateTime.now();
    if (_token == null) {
      _token = await _box.read('kb_token');
      final expires = await _box.read('kb_token_expires');
      _tokenExpires = expires == null ? null : DateTime.parse(expires);
    }
    if (_token != null && _tokenExpires != null && now.isBefore(_tokenExpires!)) return _token!;

    final body = await _post('/oauth2/token', {'Content-Type': 'application/json'},
        {'appKey': keys.appKey, 'appSecret': keys.appSecret, 'grantType': 'client_credentials'});
    final token = body['access_token'] ?? body['accessToken'];
    if (token is! String || token.isEmpty) throw BrokerError('KB 접속 토큰을 받지 못했어요. 앱키·시크리트를 확인해 주세요');
    final seconds = int.tryParse('${body['expires_in'] ?? ''}') ?? 12 * 3600;
    _token = token;
    _tokenExpires = now.add(Duration(seconds: seconds)).subtract(const Duration(minutes: 5));
    await _box.write('kb_token', token);
    await _box.write('kb_token_expires', _tokenExpires!.toIso8601String());
    return token;
  }

  /// 요청을 보내고 dataBody를 돌려준다. KB는 업무 실패도 HTTP 200으로 줄 수 있어 부르는 쪽이 값이 있는지 본다
  Future<Map<String, dynamic>> _post(String path, Map<String, String> headers, Map<String, String> dataBody) async {
    final request = http.Request('POST', Uri.parse('$kbBaseUrl$path'))
      ..headers.addAll(headers)
      ..body = jsonEncode({'dataHeader': _dataHeader, 'dataBody': dataBody});
    final response = await http.Response.fromStream(await _http.send(request).timeout(_timeout)).timeout(_timeout);
    final Object? data;
    try {
      data = jsonDecode(utf8.decode(response.bodyBytes));
    } on FormatException {
      throw BrokerError('KB 응답을 읽지 못했어요 (${response.statusCode})');
    }
    if (data is! Map<String, dynamic>) throw BrokerError('KB 응답 형식이 달라요');
    final body = data['dataBody'] is Map<String, dynamic> ? data['dataBody'] as Map<String, dynamic> : data;
    if (response.statusCode != 200) throw BrokerError('KB 오류: ${_message(data, body) ?? response.statusCode}');
    return body;
  }

  static String? _message(Map<String, dynamic> data, Map<String, dynamic> body) {
    final header = data['dataHeader'];
    final text = body['msg'] ?? (header is Map ? header['resultMessage'] ?? header['msg'] : null) ?? data['message'];
    return text is String && text.trim().isNotEmpty ? text.trim() : null;
  }

  Future<Map<String, dynamic>> _tr(String tr, Map<String, String> dataBody) async {
    final token = await _accessToken();
    return _post('/api/v1/$tr',
        {'Content-Type': 'application/json', 'appKey': keys.appKey, 'Authorization': 'bearer $token'}, dataBody);
  }

  @override
  Future<int> price(String stockCode) async {
    final body = await _tr('ivu10140', {'excg_clsf': '1', 'shrt_cd': stockCode});
    final price = int.tryParse('${body['now_prc'] ?? ''}'.trim());
    if (price == null || price <= 0) {
      throw BrokerError('KB 현재가를 받지 못했어요${body['msg'] is String ? ' (${(body['msg'] as String).trim()})' : ''}');
    }
    return price;
  }

  @override
  Future<Map<String, dynamic>?> intraday(String stockCode) async => null; // KB 분봉 TR(IVU10080 등)은 키를 붙일 때 확인

  // ---------- 아직 못 하는 것: 가짜 값 없이 실패라고 알린다 (NFR-08) ----------

  @override
  Future<Map<String, dynamic>> balance() async => throw BrokerError(_accountNotReady);

  @override
  Future<int> buyingPower() async => throw BrokerError(_accountNotReady);

  @override
  Future<List<BrokerOrder>> todayOrders(String stockCode) async => throw BrokerError(_accountNotReady);

  @override
  Future<String> revise(String orderNo, String stockCode, int? price) async =>
      throw BrokerError('KB로는 주문하지 않아요. 주문 개발·검증은 KIS 모의투자로 해요 (AGENTS.md 4장)');

  @override
  Future<({String orderNo, int filledQty, int? filledPrice})> order(String side, String stockCode, int qty, int price) async =>
      throw BrokerError('KB로는 주문하지 않아요. 주문 개발·검증은 KIS 모의투자로 해요 (AGENTS.md 4장)');
}
