// 모의투자 자동매매 (docs/plan/12-todo-by-stage.md 3-4). 모의투자(KIS 모의·가짜 증권사)에서만 켤 수 있다 (AGENTS.md 1장).
//
// 15:00~15:15에는 오늘 자동으로 산 것을 같은 흐름으로 판다 (하루 결과를 확정).
// 사는 것: 오늘 아침 브리핑에서 투자 AI가 매수 검토로 쓰고 검증 AI가 승인·조건부 승인한 종목만.
// 사는 방법: 사람이 채팅에 "○○ N주 사줘"라고 한 것과 똑같은 주문 흐름을 앱이 대신 돌린다
//   → 주문 때 다시 투자 AI → 검증 AI → 정책 검사(1회·1일 한도, 비중, 장 시간) → 처리안
//   → 처리안이 검증 승인·조건부 승인이고 따로 확인받을 것(성향 초과, 검증 반려, 급등 재확인)이 없을 때만 자동 승인
//   → 폰이 가격 재확인 후 주문. 폰 잠금 확인은 사용자가 자동매매를 켠 것으로 대신한다 (모의투자라서)
// 끄면 다음 단계부터 바로 멈춘다. 한 일은 모두 오늘 기록(log)에 남고 채팅 기록·처리안 목록에도 보인다.

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

class AutoTrader extends ChangeNotifier {
  AutoTrader({SecureBox? box, DateTime Function()? now}) : _box = box ?? secureBox, _now = now ?? DateTime.now;

  final SecureBox _box;
  final DateTime Function() _now;
  bool on = false;
  int budgetKrw = 1000000; // 하루에 자동으로 살 총액. 후보 수로 나누고, 1회 한도를 넘으면 여러 번에 나눠 산다
  List<String> log = [];
  bool _busy = false;
  Timer? _timer;

  /// 모의투자일 때만 켤 수 있다. 실전 증권사(KB 등)는 안 된다
  static bool allowed(Broker? broker) => broker != null && (broker.isFake || broker is KisMockBroker);

  String get _today => _now().toUtc().add(const Duration(hours: 9)).toIso8601String().substring(0, 10);

  Future<void> load() async {
    on = await _box.read('auto_on') == 'true';
    budgetKrw = int.tryParse(await _box.read('auto_budget_krw') ?? '') ?? budgetKrw;
    log = ((jsonDecode(await _box.read('auto_log:$_today') ?? '[]') as List)).cast<String>();
    notifyListeners();
  }

  Future<void> setOn(bool value) async {
    on = value;
    await _box.write('auto_on', '$value');
    await _note(value ? '자동매매를 켰어요 (오늘 총 ${won(budgetKrw)}, 최대 $autoMaxPerDay종목)' : '자동매매를 껐어요');
    if (value) unawaited(tick());
  }

  Future<void> setBudgetKrw(int value) async {
    budgetKrw = value;
    await _box.write('auto_budget_krw', '$value');
    notifyListeners();
  }

  /// 앱이 켜져 있는 동안 1분마다 확인한다
  void start() {
    _timer ??= Timer.periodic(const Duration(minutes: 1), (_) => tick());
    unawaited(tick());
  }

  /// 장중(09:05~15:15, 평일)이면 오늘 브리핑의 검증 통과 매수 제안 중 아직 처리 안 한 것을 산다
  Future<void> tick() async {
    if (!on || _busy || kIsWeb || !allowed(currentBroker.value)) return;
    final k = _now().toUtc().add(const Duration(hours: 9));
    final minutes = k.hour * 60 + k.minute;
    if (k.weekday > 5 || minutes < 9 * 60 + 5 || minutes > 15 * 60 + 28) return; // 휴장일은 서버 정책 검사가 막는다
    _busy = true;
    try {
      if (minutes >= 15 * 60) return await _sellAll(); // 장 마감 전: 오늘 자동으로 산 것을 판다 (오늘 결과를 확정)
      final Map<String, dynamic> briefing;
      try {
        briefing = await api.get('/api/briefings/latest') as Map<String, dynamic>;
      } on ApiError {
        return; // 아직 브리핑이 없다
      }
      if (briefing['brief_date'] != _today) return;
      final done = ((jsonDecode(await _box.read('auto_settled:$_today') ?? '[]') as List)).cast<String>();
      final tries = (jsonDecode(await _box.read('auto_tries:$_today') ?? '{}') as Map).cast<String, dynamic>();
      bool skip(Map<String, dynamic> p) => done.contains(p['stock_code']) || (tries[p['stock_code']] as int? ?? 0) >= autoMaxTries;
      final picks = ((briefing['content'] as Map)['picks'] as List).cast<Map<String, dynamic>>()
          .where((p) => const {'approve', 'conditional'}.contains(p['verdict'])).take(autoMaxPerDay).toList();
      if (picks.every(skip)) return;
      final perStock = budgetKrw ~/ picks.length;
      // 1회 한도보다 조금 작게 나눈다 (전날 종가로 수량을 정하므로 오늘 값이 오르면 한도를 넘을 수 있어서)
      final maxOrder = ((await api.get('/api/policy') as Map)['max_order_krw'] as int) * 97 ~/ 100;
      for (final pick in picks.where((p) => !skip(p))) {
        if (!on) break;
        final code = pick['stock_code'] as String;
        tries[code] = (tries[code] as int? ?? 0) + 1;
        await _box.write('auto_tries:$_today', jsonEncode(tries)); // 먼저 적어 둔다 (앱이 죽어도 횟수가 남게)
        // 이미 산 만큼은 빼고 산다 (다시 시도할 때 두 번 사지 않게)
        final already = ((await _bought())[code] as Map?)?['qty'] as int? ?? 0;
        var left = perStock - already * (pick['last_close'] as int? ?? 0);
        var failed = false;
        while (on) {
          final close = pick['last_close'] as int? ?? 0;
          final qty = close > 0 ? (left < maxOrder ? left : maxOrder) ~/ close : 0;
          if (qty < 1) break;
          final result = await _order(pick['stock_name'] as String, qty, 'buy');
          failed = result == null;
          if (result != true) break;
          await _addBought(code, pick['stock_name'] as String, qty);
          left -= qty * close;
        }
        // 오류(null)로 멈췄으면 다음 확인 때 남은 금액만큼 다시 시도한다 (하루 autoMaxTries번까지). 그 밖에는 오늘 끝
        if (!failed && on) {
          done.add(code);
          await _box.write('auto_settled:$_today', jsonEncode(done));
        }
      }
    } catch (error) {
      await _note('자동매매 중 오류: $error');
    } finally {
      _busy = false;
    }
  }

  Future<Map<String, dynamic>> _bought() async =>
      jsonDecode(await _box.read('auto_bought:$_today') ?? '{}') as Map<String, dynamic>;

  Future<void> _addBought(String code, String name, int qty) async {
    final bought = await _bought();
    bought[code] = {'name': name, 'qty': ((bought[code] as Map?)?['qty'] as int? ?? 0) + qty};
    await _box.write('auto_bought:$_today', jsonEncode(bought));
  }

  /// 15:00~15:15: 오늘 자동으로 산 종목을 지금 가진 수량 안에서 판다 (하루에 한 번)
  Future<void> _sellAll() async {
    if (await _box.read('auto_sell_done:$_today') == 'true') return;
    final bought = await _bought();
    if (bought.isEmpty) return;
    // 잔고 조회가 실패하면(시간 초과 등) 다음 확인 때 다시 한다. 조회가 된 뒤에야 오늘 판 것으로 적는다 (2026-10-08)
    final holdings = (await currentBroker.value!.balance())['holdings'] as List;
    await _box.write('auto_sell_done:$_today', 'true');
    for (final entry in bought.entries) {
      if (!on) break;
      final held = holdings.cast<Map<String, dynamic>>().where((h) => h['stock_code'] == entry.key).firstOrNull;
      final want = (entry.value as Map)['qty'] as int;
      final qty = held == null ? 0 : (held['qty'] as int) < want ? held['qty'] as int : want;
      if (qty < 1) {
        await _note('${(entry.value as Map)['name']}: 팔 수량이 없어요 (체결되지 않았거나 이미 팔았어요)');
        continue;
      }
      await _order((entry.value as Map)['name'] as String, qty, 'sell');
    }
  }

  /// 한 번 주문 (사람이 채팅에 말한 것과 같은 흐름). 자동 승인해서 실행까지 갔으면 true,
  /// 처리안이 나왔지만 자동 승인하지 않았으면 false, 처리안까지 못 갔거나 실행이 실패했으면(오류) null
  Future<bool?> _order(String name, int qty, String side) async {
    final conversation = Conversation(unlock: () async => on); // 끄면 실행 직전에도 멈춘다
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
    final k = _now().toUtc().add(const Duration(hours: 9));
    log = [...log, '${k.hour.toString().padLeft(2, '0')}:${k.minute.toString().padLeft(2, '0')} $text'];
    await _box.write('auto_log:$_today', jsonEncode(log));
    notifyListeners();
  }

}

final autoTrader = AutoTrader();
