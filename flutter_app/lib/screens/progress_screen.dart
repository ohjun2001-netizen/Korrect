import 'package:flutter/material.dart';
import '../constants.dart';
import '../services/progress_service.dart';

class ProgressScreen extends StatefulWidget {
  const ProgressScreen({super.key});

  @override
  State<ProgressScreen> createState() => _ProgressScreenState();
}

class _ProgressScreenState extends State<ProgressScreen> {
  List<SessionRecord> _history = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final history = await ProgressService.loadHistory();
    setState(() {
      _history = history.reversed.toList(); // 최신순
      _isLoading = false;
    });
  }

  Map<String, List<SessionRecord>> get _grouped {
    final map = <String, List<SessionRecord>>{};
    for (final r in _history) {
      map.putIfAbsent(r.scenarioId, () => []).add(r);
    }
    return map;
  }

  double? _avg(List<SessionRecord> records) {
    final scores = records
        .where((r) => r.totalScore != null)
        .map((r) => r.totalScore!)
        .toList();
    if (scores.isEmpty) return null;
    return scores.reduce((a, b) => a + b) / scores.length;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(AppConstants.bgColor),
      appBar: AppBar(
        backgroundColor: const Color(AppConstants.primaryColor),
        title: const Text('내 학습 기록',
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _history.isEmpty
              ? _EmptyView()
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    _SummaryCard(history: _history),
                    const SizedBox(height: 16),
                    ..._grouped.entries.map((e) => _ScenarioSection(
                          scenarioId: e.key,
                          records: e.value,
                          avgScore: _avg(e.value),
                        )),
                  ],
                ),
    );
  }
}

class _SummaryCard extends StatelessWidget {
  final List<SessionRecord> history;

  const _SummaryCard({required this.history});

  @override
  Widget build(BuildContext context) {
    final totalSessions = history.length;
    final scores = history
        .where((r) => r.totalScore != null)
        .map((r) => r.totalScore!)
        .toList();
    final avgScore =
        scores.isEmpty ? null : scores.reduce((a, b) => a + b) / scores.length;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(AppConstants.primaryColor),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _SummaryItem(label: '총 연습', value: '$totalSessions회'),
          Container(width: 1, height: 40, color: Colors.white30),
          _SummaryItem(
            label: '평균 점수',
            value: avgScore != null ? '${avgScore.toInt()}점' : '-',
          ),
          Container(width: 1, height: 40, color: Colors.white30),
          _SummaryItem(
            label: '연습한 상황',
            value: '${history.map((r) => r.scenarioId).toSet().length}개',
          ),
        ],
      ),
    );
  }
}

class _SummaryItem extends StatelessWidget {
  final String label;
  final String value;

  const _SummaryItem({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(value,
            style: const TextStyle(
                color: Colors.white,
                fontSize: 22,
                fontWeight: FontWeight.bold)),
        const SizedBox(height: 4),
        Text(label,
            style: const TextStyle(color: Colors.white70, fontSize: 12)),
      ],
    );
  }
}

class _ScenarioSection extends StatelessWidget {
  final String scenarioId;
  final List<SessionRecord> records;
  final double? avgScore;

  const _ScenarioSection({
    required this.scenarioId,
    required this.records,
    required this.avgScore,
  });

  String get _emoji =>
      AppConstants.scenarioEmoji[scenarioId] ?? '💬';

  Color get _avgColor {
    if (avgScore == null) return Colors.grey;
    if (avgScore! >= 80) return Colors.green;
    if (avgScore! >= 60) return Colors.orange;
    return Colors.redAccent;
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(_emoji, style: const TextStyle(fontSize: 20)),
            const SizedBox(width: 8),
            Text(records.first.scenarioTitle,
                style: const TextStyle(
                    fontSize: 16, fontWeight: FontWeight.bold)),
            const Spacer(),
            if (avgScore != null)
              Text('평균 ${avgScore!.toInt()}점',
                  style: TextStyle(
                      color: _avgColor, fontWeight: FontWeight.w600)),
          ],
        ),
        const SizedBox(height: 8),
        ...records.map((r) => _SessionTile(record: r)),
        const SizedBox(height: 16),
      ],
    );
  }
}

class _SessionTile extends StatelessWidget {
  final SessionRecord record;

  const _SessionTile({required this.record});

  String _formatDate(DateTime dt) {
    return '${dt.month}/${dt.day} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
  }

  Color get _scoreColor {
    if (record.totalScore == null) return Colors.grey;
    if (record.totalScore! >= 80) return Colors.green;
    if (record.totalScore! >= 60) return Colors.orange;
    return Colors.redAccent;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withValues(alpha: 0.04), blurRadius: 4),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(_formatDate(record.date),
                    style: const TextStyle(fontSize: 12, color: Colors.grey)),
                const SizedBox(height: 2),
                Text('${record.turnCount}번 대화',
                    style: const TextStyle(fontSize: 13)),
              ],
            ),
          ),
          if (record.totalScore != null)
            Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              decoration: BoxDecoration(
                color: _scoreColor,
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                '${record.totalScore!.toInt()}점',
                style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 14),
              ),
            )
          else
            const Text('-', style: TextStyle(color: Colors.grey)),
        ],
      ),
    );
  }
}

class _EmptyView extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text('📚', style: TextStyle(fontSize: 64)),
          SizedBox(height: 16),
          Text('아직 연습 기록이 없어요!',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          SizedBox(height: 8),
          Text('시나리오를 골라서 연습해봐요 😊',
              style: TextStyle(fontSize: 14, color: Colors.grey)),
        ],
      ),
    );
  }
}
