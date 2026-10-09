// 모의투자 자동매매 (docs/plan/12-todo-by-stage.md 3-4). 모의투자(KIS 모의·가짜 증권사)에서만 켤 수 있다 (AGENTS.md 1장).
//
// 매일 사용자 승인이 먼저다: 그날 "오늘 계획"(살 총액, 팔 종목)을 사용자가 승인해야 사고판다. 승인이 없으면 아무것도 안 한다.
// 사는 것: 오늘 아침 브리핑에서 투자 AI가 매수 검토로 쓰고 검증 AI가 승인·조건부 승인한 종목만, 승인한 총액 안에서.
// 파는 것: 자동매매로 산 종목(전날 이전 것 포함) 중 사용자가 오늘 팔기로 고른 것만, 15:00~15:28에.
// 사고파는 방법: 사람이 채팅에 "○○ N주 사줘/팔아줘"라고 한 것과 똑같은 주문 흐름을 앱이 대신 돌린다
//   → 주문 때 다시 투자 AI → 검증 AI → 정책 검사(1회 한도, 비중, 장 시간) → 처리안
//   → 처리안이 검증 승인·조건부 승인이고 따로 확인받을 것(성향 초과, 검증 반려, 급등 재확인)이 없을 때만 자동 승인
//   → 폰이 가격 재확인 후 주문. 폰 잠금 확인은 사용자가 자동매매를 켜고 오늘 계획을 승인한 것으로 대신한다 (모의투자라서)
// 장중 급락 매도(사용자가 오늘 계획에서 허용했을 때): 자동매매로 산 종목이 매입가보다 autoDropPct% 넘게 내리면
//   투자 AI에게 "지금 팔아야 할까?"를 분석시키고(검증 AI가 다시 확인), 제안이 '매도 검토'이고 검증이 승인·조건부 승인일 때만
//   같은 주문 흐름으로 판다. 아니면 들고 있는다. 같은 종목은 30분에 한 번, 하루 3번까지만 묻는다 (Gemini 비용)
// 1회 한도를 넘는 금액은 사든 팔든 여러 번에 나눠 주문한다. 끄면 다음 단계부터 바로 멈춘다. 한 일은 모두 오늘 기록(log)에 남는다.

import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';

import '../../api/api.dart';
import '../../broker/broker.dart';
import '../../broker/kis_mock_broker.dart';
import '../../secure/key_store.dart';
import '../chat/conversation.dart';
import '../../common/common.dart';

const autoMaxPerDay = 3; // 하루에 자동으로 사는 종목 수 (아침 브리핑 후보도 최대 3개)
const autoMaxTries = 3; // 처리안까지 못 간 오류(서버·통신)는 종목마다 하루 이만큼 다시 시도한다
const autoBudgets = [0, 1000000, 3000000, 5000000]; // 0 = 오늘은 사지 않음
const autoDropPct = 3; // 매입가보다 이만큼(%) 넘게 내리면 AI에게 매도 판단을 묻는다
const autoReviewGap = Duration(minutes: 30);
const autoMaxReviews = 3; // 종목마다 하루에 묻는 횟수
const _watchGap = Duration(minutes: 5); // 잔고 조회가 느려서(모의 12초) 5분마다만 본다

/// 분석 답의 첫 두 줄("… 분석 · 검증: 승인", "제안: 매도 검토")로 AI가 지금 팔자고 했는지 본다
/// ponytail: 서버 답 문장(analysis.format_analysis)에 기댄다. 문장이 바뀌면 여기와 테스트가 같이 깨진다
bool aiSaysSell(String analysis) {
  final lines = analysis.split('\n');
  if (lines.length < 2) return false;
  final verified = lines[0].endsWith('검증: 승인') || lines[0].endsWith('검증: 조건부 승인');
  return verified && lines[1].trim() == '제안: 매도 검토';
}

/// qty주를 1회 한도(maxOrder원) 안으로 나눈 주문 수량들. 1주 값이 한도보다 비싸면 빈 목록
List<int> splitQty(int qty, int price, int maxOrder) {
  final chunk = price > 0 ? maxOrder ~/ price : 0;
  if (chunk < 1) return [];
  return [for (var left = qty; left > 0; left -= chunk) left < chunk ? left : chunk];
}

class AutoTrader extends ChangeNotifier {
  AutoTrader({SecureBox? box, DateTime Function()? now}) : _box = box ?? secureBox, _now = now ?? DateTime.now;

  final SecureBox _box;
  final DateTime Function() _now;
  bool on = false;
  int budgetKrw = 1000000; // 오늘 계획을 고를 때 처음 보여 줄 총액 (지난번 승인한 값)
  List<String> log = [];
  Map<String, dynamic>? plan; // 오늘 승인한 계획 {budget: 원, sell: [종목코드]}. null이면 아직 승인 안 함
  Map<String, dynamic> positions = {}; // 자동매매로 사서 아직 안 판 것 {종목코드: {name, qty}} (날짜를 넘겨 남는다)
  bool _busy = false;
  Timer? _timer;
  DateTime? _lastWatch;

  /// 모의투자일 때만 켤 수 있다. 실전 증권사(KB 등)는 안 된다
  static bool allowed(Broker? broker) => broker != null && (broker.isFake || broker is KisMockBroker);

  DateTime get _kst => _now().toUtc().add(const Duration(hours: 9));
  String get _today => _kst.toIso8601String().substring(0, 10);

  /// 켜져 있고 평일인데 오늘 계획을 아직 승인하지 않았다 (화면이 사용자에게 묻는다)
  bool get needsPlan => on && plan == null && _kst.weekday <= 5;

  Future<void> load() async {
    on = await _box.read('auto_on') == 'true';
    budgetKrw = int.tryParse(await _box.read('auto_budget_krw') ?? '') ?? budgetKrw;
    log = ((jsonDecode(await _box.read('auto_log:$_today') ?? '[]') as List)).cast<String>();
    final saved = await _box.read('auto_plan:$_today');
    plan = saved == null ? null : jsonDecode(saved) as Map<String, dynamic>;
    final held = await _box.read('auto_positions');
    positions = held != null ? jsonDecode(held) as Map<String, dynamic> : await _legacyPositions();
    notifyListeners();
  }

  /// 예전 형식(그날 산 것만 auto_bought:날짜에 적던 때)에서 최근 2주치를 옮긴다
  Future<Map<String, dynamic>> _legacyPositions() async {
    final merged = <String, dynamic>{};
    for (var d = 0; d < 14; d++) {
      final day = _kst.subtract(Duration(days: d)).toIso8601String().substring(0, 10);
      final bought = jsonDecode(await _box.read('auto_bought:$day') ?? '{}') as Map<String, dynamic>;
      for (final e in bought.entries) {
        final qty = ((merged[e.key] as Map?)?['qty'] as int? ?? 0) + ((e.value as Map)['qty'] as int);
        merged[e.key] = {'name': (e.value as Map)['name'], 'qty': qty};
      }
    }
    if (merged.isNotEmpty) await _box.write('auto_positions', jsonEncode(merged));
    return merged;
  }

  Future<void> setOn(bool value) async {
    on = value;
    await _box.write('auto_on', '$value');
    await _note(value ? '자동매매를 켰어요. 오늘 계획을 승인하면 시작해요' : '자동매매를 껐어요');
    if (value) unawaited(tick());
  }

  /// 사용자가 오늘 계획을 승인했다: 살 총액(0이면 안 삼), 15:00 이후 팔 종목, 장중 급락 시 AI 판단 매도 허용
  Future<void> approvePlan(int budget, List<String> sell, {bool aiSell = true}) async {
    plan = {'budget': budget, 'sell': sell, 'ai_sell': aiSell};
    if (budget > 0) budgetKrw = budget;
    await _box.write('auto_plan:$_today', jsonEncode(plan));
    await _box.write('auto_budget_krw', '$budgetKrw');
    final names = [for (final c in sell) (positions[c] as Map?)?['name'] ?? c];
    await _note('오늘 계획 승인: ${budget > 0 ? '${won(budget)}까지 매수' : '매수 안 함'}'
        '${names.isEmpty ? '' : ', 15:00 이후 ${names.join('·')} 매도'}'
        '${aiSell ? ', 장중 급락 시 AI 판단 매도' : ''}');
    unawaited(tick());
  }

  /// 오늘 계획을 거둔다. 이미 낸 주문은 그대로고 다음 단계부터 멈춘다
  Future<void> cancelPlan() async {
    plan = null;
    await _box.delete('auto_plan:$_today');
    await _note('오늘 계획을 취소했어요');
  }

  /// 앱이 켜져 있는 동안 1분마다 확인한다
  void start() {
    _timer ??= Timer.periodic(const Duration(minutes: 1), (_) => tick());
    unawaited(tick());
  }

  /// 장중(09:05~15:28, 평일)이고 오늘 계획을 승인했으면: 15:00 전에는 사고, 15:00부터는 고른 종목을 판다
  Future<void> tick() async {
    if (!on || _busy || kIsWeb || !allowed(currentBroker.value)) return;
    final k = _kst;
    final minutes = k.hour * 60 + k.minute;
    if (k.weekday > 5 || minutes < 9 * 60 + 5 || minutes > 15 * 60 + 28) return; // 휴장일은 서버 정책 검사가 막는다
    if (plan == null) return; // 사용자가 오늘 계획을 승인하기 전에는 아무것도 하지 않는다
    _busy = true;
    try {
      if (minutes >= 15 * 60) return await _sellAll();
      await _buy(plan!['budget'] as int);
      if (plan?['ai_sell'] == true) await _watchDrops();
    } catch (error) {
      await _note('자동매매 중 오류: $error');
    } finally {
      _busy = false;
    }
  }

  /// 1회 한도보다 조금 작게 (전날 종가로 수량을 정하므로 오늘 값이 오르면 한도를 넘을 수 있어서)
  Future<int> _maxOrder() async => ((await api.get('/api/policy') as Map)['max_order_krw'] as int) * 97 ~/ 100;

  Future<void> _buy(int budget) async {
    if (budget <= 0) return;
    final Map<String, dynamic> briefing;
    try {
      briefing = await api.get('/api/briefings/latest') as Map<String, dynamic>;
    } on ApiError {
      return; // 아직 브리핑이 없다
    }
    if (briefing['brief_date'] != _today) return;
    final done = ((jsonDecode(await _box.read('auto_settled:$_today') ?? '[]') as List)).cast<String>();
    final tries = (jsonDecode(await _box.read('auto_tries:$_today') ?? '{}') as Map).cast<String, dynamic>();
    final bought = (jsonDecode(await _box.read('auto_bought:$_today') ?? '{}') as Map).cast<String, dynamic>();
    bool skip(Map<String, dynamic> p) => done.contains(p['stock_code']) || (tries[p['stock_code']] as int? ?? 0) >= autoMaxTries;
    final picks = ((briefing['content'] as Map)['picks'] as List).cast<Map<String, dynamic>>()
        .where((p) => const {'approve', 'conditional'}.contains(p['verdict'])).take(autoMaxPerDay).toList();
    if (picks.every(skip)) return;
    final perStock = budget ~/ picks.length;
    final maxOrder = await _maxOrder();
    for (final pick in picks.where((p) => !skip(p))) {
      if (!on || plan == null) break;
      final code = pick['stock_code'] as String, name = pick['stock_name'] as String;
      final close = pick['last_close'] as int? ?? 0;
      tries[code] = (tries[code] as int? ?? 0) + 1;
      await _box.write('auto_tries:$_today', jsonEncode(tries)); // 먼저 적어 둔다 (앱이 죽어도 횟수가 남게)
      // 오늘 이미 산 만큼은 빼고 산다 (다시 시도할 때 두 번 사지 않게)
      var left = perStock - ((bought[code] as Map?)?['qty'] as int? ?? 0) * close;
      var failed = false;
      while (on && plan != null) {
        final qty = close > 0 ? (left < maxOrder ? left : maxOrder) ~/ close : 0;
        if (qty < 1) break;
        final result = await _order(name, qty, 'buy');
        failed = result == null;
        if (result != true) break;
        bought[code] = {'name': name, 'qty': ((bought[code] as Map?)?['qty'] as int? ?? 0) + qty};
        await _box.write('auto_bought:$_today', jsonEncode(bought));
        await _addPosition(code, name, qty);
        left -= qty * close;
      }
      // 오류(null)로 멈췄으면 다음 확인 때 남은 금액만큼 다시 시도한다 (하루 autoMaxTries번까지). 그 밖에는 오늘 끝
      if (!failed && on && plan != null) {
        done.add(code);
        await _box.write('auto_settled:$_today', jsonEncode(done));
      }
    }
  }

  Future<void> _addPosition(String code, String name, int qty) async {
    final left = ((positions[code] as Map?)?['qty'] as int? ?? 0) + qty;
    if (left > 0) {
      positions[code] = {'name': name, 'qty': left};
    } else {
      positions.remove(code);
    }
    await _box.write('auto_positions', jsonEncode(positions));
    notifyListeners();
  }

  /// 장중 급락 감시: 자동매매로 산 종목이 매입가보다 autoDropPct% 넘게 내렸으면 AI에게 매도 판단을 묻고, 팔자고 하면 판다
  Future<void> _watchDrops() async {
    if (positions.isEmpty || (_lastWatch != null && _now().difference(_lastWatch!) < _watchGap)) return;
    _lastWatch = _now();
    final broker = currentBroker.value!;
    final holdings = ((await broker.balance())['holdings'] as List).cast<Map<String, dynamic>>();
    final reviews = (jsonDecode(await _box.read('auto_reviews:$_today') ?? '{}') as Map).cast<String, dynamic>();
    for (final code in positions.keys.toList()) {
      if (!on || plan == null) break;
      final held = holdings.where((h) => h['stock_code'] == code).firstOrNull;
      final avg = held?['avg_price'] as int? ?? 0;
      final price = broker.lastPrices[code] ?? 0;
      if (held == null || avg <= 0 || price <= 0) continue;
      final drop = (price - avg) * 100 / avg;
      final seen = (reviews[code] as Map?)?.cast<String, dynamic>() ?? {};
      final last = DateTime.tryParse(seen['at'] as String? ?? '');
      if (drop > -autoDropPct || (seen['n'] as int? ?? 0) >= autoMaxReviews ||
          (last != null && _now().difference(last) < autoReviewGap)) {
        continue;
      }
      reviews[code] = {'n': (seen['n'] as int? ?? 0) + 1, 'at': _now().toIso8601String()};
      await _box.write('auto_reviews:$_today', jsonEncode(reviews)); // 먼저 적어 둔다 (실패해도 30분은 다시 안 묻는다)
      final name = (positions[code] as Map)['name'] as String;
      await _note('$name 매입가 대비 ${drop.toStringAsFixed(1)}%: 투자 AI·검증 AI에게 매도 판단을 물어요');
      final conversation = Conversation(unlock: () async => false); // 분석만 한다. 주문은 아래에서 따로
      await conversation.send('$name 지금 팔아야 할까? 매입가 ${won(avg)}보다 ${drop.toStringAsFixed(1)}% 내렸어');
      final answer = conversation.items.lastWhere((i) => i.role != 'user', orElse: () => ChatItem('info', '')).text;
      if (!aiSaysSell(answer)) {
        await _note('$name: AI 판단은 매도가 아니에요 (${answer.split('\n').take(2).join(' / ')}). 들고 있어요');
        continue;
      }
      final mine = (positions[code] as Map)['qty'] as int;
      final qty = (held['qty'] as int) < mine ? held['qty'] as int : mine;
      await _note('$name: AI가 매도를 제안했고 검증 AI가 승인했어요. $qty주를 팔아요');
      for (final part in splitQty(qty, price, await _maxOrder())) {
        if (!on || plan == null || await _order(name, part, 'sell') != true) break;
        await _addPosition(code, name, -part);
      }
    }
  }

  /// 15:00~15:28: 오늘 계획에서 고른 종목을, 자동으로 산 수량과 지금 가진 수량 중 작은 만큼 1회 한도 안으로 나눠 판다
  Future<void> _sellAll() async {
    final sell = ((plan!['sell'] as List?) ?? []).cast<String>();
    if (sell.isEmpty || await _box.read('auto_sell_done:$_today') == 'true') return;
    // 잔고 조회가 실패하면(시간 초과 등) 다음 확인 때 다시 한다. 조회가 된 뒤에야 오늘 판 것으로 적는다 (2026-10-08)
    final broker = currentBroker.value!;
    final holdings = ((await broker.balance())['holdings'] as List).cast<Map<String, dynamic>>();
    await _box.write('auto_sell_done:$_today', 'true');
    final maxOrder = await _maxOrder();
    for (final code in sell) {
      if (!on || plan == null) break;
      final mine = positions[code] as Map?;
      final name = mine?['name'] as String? ?? code;
      final held = holdings.where((h) => h['stock_code'] == code).firstOrNull?['qty'] as int? ?? 0;
      final want = mine?['qty'] as int? ?? 0;
      final qty = held < want ? held : want;
      if (qty < 1) {
        await _note('$name: 팔 수량이 없어요 (체결되지 않았거나 이미 팔았어요)');
        continue;
      }
      final parts = splitQty(qty, await broker.price(code), maxOrder);
      if (parts.isEmpty) await _note('$name: 1주 값이 1회 한도보다 커서 팔 수 없어요. 직접 판단해 주세요');
      for (final part in parts) {
        if (!on || plan == null || await _order(name, part, 'sell') != true) break;
        await _addPosition(code, name, -part);
      }
    }
  }

  /// 한 번 주문 (사람이 채팅에 말한 것과 같은 흐름). 자동 승인해서 실행까지 갔으면 true,
  /// 처리안이 나왔지만 자동 승인하지 않았으면 false, 처리안까지 못 갔거나 실행이 실패했으면(오류) null
  Future<bool?> _order(String name, int qty, String side) async {
    final conversation = Conversation(unlock: () async => on && plan != null); // 끄거나 계획을 거두면 실행 직전에도 멈춘다
    await conversation.send(side == 'buy' ? '$name $qty주 사줘' : '$name $qty주 팔아줘');
    final waiting = conversation.waiting;
    if (waiting?['kind'] != 'approval') {
      await _note('$name $qty주: ${_last(conversation)}');
      return null;
    }
    final card = waiting!['card'] as Map<String, dynamic>;
    final confirm = (card['confirm_required'] as List).cast<String>();
    if (!on || confirm.isNotEmpty || !const {'approve', 'conditional'}.contains(card['verdict'])) {
      await _note('$name $qty주: 자동으로 승인하지 않았어요 (${confirm.isNotEmpty ? confirm.join(' ') : '검증 ${card['verdict']}'}). '
          '처리안 모아보기에서 직접 판단해 주세요');
      return false;
    }
    await conversation.answer({'decision': 'approve'});
    final result = _last(conversation);
    await _note('$name $qty주 자동 ${side == 'buy' ? '매수' : '매도'}: $result');
    // 실행 실패는 처리안을 다 쓴 것이라 다시 시도해도 중복 주문이 남지 않는다
    return result.contains('실패') ? null : !result.contains('않았어요');
  }

  String _last(Conversation c) =>
      c.items.lastWhere((i) => i.role != 'user', orElse: () => ChatItem('info', '응답 없음')).text.split('\n').first;

  Future<void> _note(String text) async {
    final k = _kst;
    log = [...log, '${k.hour.toString().padLeft(2, '0')}:${k.minute.toString().padLeft(2, '0')} $text'];
    await _box.write('auto_log:$_today', jsonEncode(log));
    notifyListeners();
  }
}

final autoTrader = AutoTrader();
