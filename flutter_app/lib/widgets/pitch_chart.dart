import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

class PitchChart extends StatelessWidget {
  final List<double> userPitch;
  final List<double> refPitch;

  const PitchChart({
    super.key,
    required this.userPitch,
    required this.refPitch,
  });

  List<FlSpot> _toSpots(List<double> pitchList) {
    if (pitchList.isEmpty) return [];
    final voiced = <FlSpot>[];
    final total = pitchList.length;
    final step = total > 100 ? total ~/ 100 : 1;
    for (int i = 0; i < total; i += step) {
      if (pitchList[i] > 0) {
        // x축을 0~100으로 정규화해서 길이가 달라도 같은 위치에 겹치게
        final x = i / (total - 1) * 100;
        voiced.add(FlSpot(x, pitchList[i]));
      }
    }
    return voiced;
  }

  @override
  Widget build(BuildContext context) {
    final userSpots = _toSpots(userPitch);
    final refSpots = _toSpots(refPitch);

    if (userSpots.isEmpty) {
      return const Center(child: Text('피치 데이터가 없어요'));
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 범례
        Row(
          children: [
            _LegendItem(color: Colors.blue, label: '내 목소리'),
            const SizedBox(width: 16),
            if (refSpots.isNotEmpty)
              _LegendItem(color: Colors.orange, label: '원어민'),
          ],
        ),
        const SizedBox(height: 8),
        SizedBox(
          height: 150,
          child: LineChart(
            LineChartData(
              gridData: const FlGridData(show: false),
              titlesData: FlTitlesData(
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    getTitlesWidget: (value, meta) => Text(
                      '${value.toInt()}Hz',
                      style: const TextStyle(fontSize: 9),
                    ),
                    reservedSize: 40,
                  ),
                ),
                bottomTitles: const AxisTitles(
                  sideTitles: SideTitles(showTitles: false),
                ),
                rightTitles: const AxisTitles(
                  sideTitles: SideTitles(showTitles: false),
                ),
                topTitles: const AxisTitles(
                  sideTitles: SideTitles(showTitles: false),
                ),
              ),
              borderData: FlBorderData(show: false),
              lineBarsData: [
                // 사용자 피치 (파란색)
                LineChartBarData(
                  spots: userSpots,
                  isCurved: true,
                  color: Colors.blue,
                  barWidth: 2,
                  dotData: const FlDotData(show: false),
                ),
                // 레퍼런스 피치 (주황색)
                if (refSpots.isNotEmpty)
                  LineChartBarData(
                    spots: refSpots,
                    isCurved: true,
                    color: Colors.orange,
                    barWidth: 2,
                    dotData: const FlDotData(show: false),
                    dashArray: [5, 3],
                  ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _LegendItem extends StatelessWidget {
  final Color color;
  final String label;

  const _LegendItem({required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 16,
          height: 3,
          color: color,
        ),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(fontSize: 12)),
      ],
    );
  }
}
