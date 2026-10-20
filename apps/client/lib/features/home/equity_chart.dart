// 자산 탭 총자산 그래프: 오늘(장중, 자동매매가 5분마다·자산 탭을 열 때) / 날짜별(그날 마지막 값).
// 값은 폰이 현재가로 계산해 스냅샷과 함께 서버에 올린 것 (GET /api/equity). 서버엔 실시간 시세가 없다.

import 'package:flutter/material.dart';

import '../../api/api.dart';
import '../../common/common.dart';
import 'overview.dart';

/// 그래프에 쓸 (이름표, 총자산) 목록. 장중은 "HH:MM", 날짜별은 "M/D"
List<(String, int)> equitySeries(Map<String, dynamic> data, {required bool daily}) => daily
    ? [
        for (final d in (data['days'] as List).cast<Map<String, dynamic>>())
          (monthDay(d['date'] as String), d['total_krw'] as int),
      ]
    : [
        for (final p in ((data['intraday'] as Map)['points'] as List).cast<Map<String, dynamic>>())
          (p['time'] as String, p['total_krw'] as int),
      ];

/// "2026-10-19" → "10/19"
String monthDay(String ymd) => '${int.parse(ymd.substring(5, 7))}/${int.parse(ymd.substring(8, 10))}';

class EquityCard extends StatefulWidget {
  const EquityCard({super.key});

  @override
  State<EquityCard> createState() => _EquityCardState();
}

class _EquityCardState extends State<EquityCard> {
  late Future<Map<String, dynamic>> _data = _load(null);
  bool _daily = false;

  Future<Map<String, dynamic>> _load(String? day) =>
      api.get(day == null ? '/api/equity' : '/api/equity?day=$day').then((value) => value as Map<String, dynamic>);

  /// 달력에서 기록이 있는 날만 고를 수 있다. 고르면 그날 장중 그래프
  Future<void> _pickDay(Map<String, dynamic> data) async {
    final days = {for (final d in (data['days'] as List).cast<Map<String, dynamic>>()) d['date'] as String};
    if (days.isEmpty) return;
    final shown = (data['intraday'] as Map)['date'] as String? ?? days.last;
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime.parse(shown),
      firstDate: DateTime.parse(days.first),
      lastDate: DateTime.parse(days.last),
      selectableDayPredicate: (d) => days.contains(d.toIso8601String().substring(0, 10)),
      helpText: '장중 그래프를 볼 날짜',
    );
    if (picked == null || !mounted) return;
    setState(() {
      _daily = false;
      _data = _load(picked.toIso8601String().substring(0, 10));
    });
  }

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 14),
          child: FutureBuilder(
            future: _data,
            builder: (context, snapshot) {
              final data = snapshot.data;
              final day = (data?['intraday'] as Map?)?['date'] as String?;
              return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  const Text('총자산 흐름', style: TextStyle(fontWeight: FontWeight.bold)),
                  const Spacer(),
                  for (final (label, daily) in [(day == null ? '장중' : '${monthDay(day)} 장중', false), ('날짜별', true)])
                    Padding(
                      padding: const EdgeInsets.only(left: 6),
                      child: ChoiceChip(
                        label: Text(label, style: const TextStyle(fontSize: 12)),
                        visualDensity: VisualDensity.compact,
                        selected: _daily == daily,
                        onSelected: (_) => setState(() => _daily = daily),
                      ),
                    ),
                  IconButton(
                    tooltip: '날짜 고르기',
                    visualDensity: VisualDensity.compact,
                    icon: const Icon(Icons.calendar_month_outlined, size: 20),
                    onPressed: data == null ? null : () => _pickDay(data),
                  ),
                ]),
                const SizedBox(height: 8),
                if (snapshot.hasError)
                  const Text('기록을 불러오지 못했어요', style: TextStyle(color: mutedText))
                else if (data == null)
                  const SizedBox(height: 140, child: Center(child: CircularProgressIndicator()))
                else
                  _chart(equitySeries(data, daily: _daily)),
              ]);
            },
          ),
        ),
      );

  Widget _chart(List<(String, int)> series) {
    if (series.length < 2) {
      return const SizedBox(
        height: 80,
        child: Center(child: Text('기록이 두 개 이상 쌓이면 그래프가 보여요', style: TextStyle(color: mutedText))),
      );
    }
    final first = series.first.$2, last = series.last.$2;
    final color = changeColor(last - first) ?? brandBlue;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text('${series.first.$1} 대비 ${signedWon(last - first)} (${rateText(last - first, first)})',
          style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: color)),
      const SizedBox(height: 8),
      SizedBox(
        height: 140,
        width: double.infinity,
        child: CustomPaint(painter: _Line([for (final (_, v) in series) v], color)),
      ),
      const SizedBox(height: 4),
      Row(children: [
        Text(series.first.$1, style: const TextStyle(fontSize: 11, color: mutedText)),
        const Spacer(),
        Text('${series.last.$1} · ${won(last)}', style: const TextStyle(fontSize: 11, color: mutedText)),
      ]),
    ]);
  }
}

/// 선 그래프: 첫 값 높이에 점선(기준선), 마지막 값에 점. 위아래 끝에 최고·최저 금액
class _Line extends CustomPainter {
  _Line(this.values, this.color);
  final List<int> values;
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final hi = values.reduce((a, b) => a > b ? a : b), lo = values.reduce((a, b) => a < b ? a : b);
    final span = hi == lo ? 1 : hi - lo;
    const top = 14.0, bottom = 14.0;
    Offset at(int i) => Offset(size.width * i / (values.length - 1),
        top + (size.height - top - bottom) * (hi - values[i]) / span);

    final base = at(0).dy;
    final dash = Paint()..color = mutedText.withValues(alpha: 0.4)..strokeWidth = 1;
    for (var x = 0.0; x < size.width; x += 8) {
      canvas.drawLine(Offset(x, base), Offset(x + 4, base), dash);
    }
    final path = Path()..moveTo(at(0).dx, at(0).dy);
    for (var i = 1; i < values.length; i++) {
      path.lineTo(at(i).dx, at(i).dy);
    }
    canvas.drawPath(path, Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2
      ..strokeJoin = StrokeJoin.round);
    canvas.drawCircle(at(values.length - 1), 4, Paint()..color = color);
    for (final (value, y) in [(hi, 0.0), (lo, size.height - 12)]) {
      (TextPainter(text: TextSpan(text: won(value), style: const TextStyle(fontSize: 10, color: mutedText)),
              textDirection: TextDirection.ltr)
            ..layout())
          .paint(canvas, Offset(0, y));
    }
  }

  @override
  bool shouldRepaint(_Line old) => old.values != values || old.color != color;
}
