// 공통: 금액 표시, 색, 시각, 배지 (docs/plan/03-screens.md 3장 공통 규칙)

import 'package:flutter/material.dart';

import '../api/api.dart';

/// 천 단위 콤마 (1250000 → 1,250,000)
String comma(num value) {
  final digits = value.round().abs().toString();
  final out = StringBuffer(value < 0 ? '-' : '');
  for (var i = 0; i < digits.length; i++) {
    if (i > 0 && (digits.length - i) % 3 == 0) out.write(',');
    out.write(digits[i]);
  }
  return out.toString();
}

String won(num value) => '${comma(value)}원';

/// 상승·이익 빨강, 하락·손실 파랑
Color? changeColor(num value) => value > 0 ? Colors.red : value < 0 ? Colors.blue : null;

/// 서버 시각(ISO) → 이 기기 시각 "10:32"
String hhmm(String iso) {
  final t = DateTime.parse(iso).toLocal();
  return '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';
}

const verdictLabels = {'approve': '승인', 'conditional': '조건부 승인', 'reject': '반려', 'user_judgement': '사용자 판단 필요'};
const verdictColors = {
  'approve': Colors.green,
  'conditional': Colors.amber,
  'reject': Colors.red,
  'user_judgement': Colors.grey,
};
const sideLabels = {'buy': '매수', 'sell': '매도'};

/// 성향 모드. 일반 모드면 모든 화면 위에 배지를 띄운다. 로그인·퀴즈·설정에서 갱신한다
final profileMode = ValueNotifier<String>('general');

Future<void> refreshProfileMode() async {
  final profile = await api.get('/api/profile');
  profileMode.value = profile['mode'] as String;
}

class Tag extends StatelessWidget {
  const Tag(this.label, this.color, {super.key});
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
        decoration: BoxDecoration(color: color.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(10)),
        child: Text(label, style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.bold)),
      );
}

/// 모든 화면 맨 위: 모의투자 배지(MVP는 항상 모의) + 일반 모드 배지
AppBar topBar(String title, {List<Widget> actions = const []}) => AppBar(
      title: Text(title),
      actions: [
        ValueListenableBuilder(
          valueListenable: profileMode,
          builder: (_, mode, _) => mode == 'general' ? const Tag('일반 모드', Colors.blueGrey) : const SizedBox(),
        ),
        const SizedBox(width: 6),
        const Tag('모의투자', Colors.teal),
        const SizedBox(width: 8),
        ...actions,
      ],
    );

/// 출처·기준 시각 ("가짜 증권사 · 10:32 기준")
class SourceText extends StatelessWidget {
  const SourceText(this.text, {super.key});
  final String text;

  @override
  Widget build(BuildContext context) =>
      Text(text, style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.outline));
}

void showError(BuildContext context, Object error) {
  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error.toString())));
}

/// 실패를 정직하게 보여주고 다시 시도 버튼을 둔다 (가짜 숫자 없이)
class ErrorRetry extends StatelessWidget {
  const ErrorRetry(this.error, this.onRetry, {super.key});
  final Object error;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Center(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text(error.toString(), textAlign: TextAlign.center),
          const SizedBox(height: 8),
          OutlinedButton(onPressed: onRetry, child: const Text('다시 시도')),
        ]),
      );
}
