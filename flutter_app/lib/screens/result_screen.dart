import 'package:flutter/material.dart';
import '../constants.dart';
import '../models/scenario_model.dart';
import '../services/progress_service.dart';
import 'home_screen.dart';

class ResultScreen extends StatelessWidget {
  final Scenario scenario;
  final double? totalScore;
  final int turnCount;
  final double? rhythmScore;
  final double? stressScore;
  final double? mfccScore;

  ResultScreen({
    super.key,
    required this.scenario,
    required this.totalScore,
    required this.turnCount,
    this.rhythmScore,
    this.stressScore,
    this.mfccScore,
  }) {
    ProgressService.saveSession(SessionRecord(
      scenarioId: scenario.id,
      scenarioTitle: scenario.title,
      totalScore: totalScore,
      rhythmScore: rhythmScore,
      stressScore: stressScore,
      mfccScore: mfccScore,
      turnCount: turnCount,
      date: DateTime.now(),
    ));
  }

  String get _emoji {
    if (totalScore == null) return '🎉';
    if (totalScore! >= 80) return '🏆';
    if (totalScore! >= 60) return '😊';
    return '💪';
  }

  String get _message {
    if (totalScore == null) return '오늘도 열심히 연습했어요!';
    if (totalScore! >= 80) return '완벽해요! 정말 잘했어요!';
    if (totalScore! >= 60) return '잘하고 있어요! 조금 더 연습해봐요!';
    return '괜찮아요! 계속 연습하면 잘 할 수 있어요!';
  }

  Color get _scoreColor {
    if (totalScore == null) return Colors.grey;
    if (totalScore! >= 80) return Colors.green;
    if (totalScore! >= 60) return Colors.orange;
    return Colors.red;
  }

  bool get _hasSubScores =>
      rhythmScore != null && stressScore != null && mfccScore != null;

  @override
  Widget build(BuildContext context) {
    final scenarioEmoji = AppConstants.scenarioEmoji[scenario.id] ?? '💬';

    return Scaffold(
      backgroundColor: const Color(AppConstants.bgColor),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const SizedBox(height: 24),

              // 결과 이모지
              Text(_emoji, style: const TextStyle(fontSize: 72)),
              const SizedBox(height: 16),

              const Text(
                '연습 완료!',
                style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),

              Text(
                '$scenarioEmoji ${scenario.title} 대화 연습',
                style: TextStyle(fontSize: 16, color: Colors.grey[600]),
              ),
              const SizedBox(height: 32),

              // 점수 카드
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.08),
                      blurRadius: 10,
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    const Text(
                      '억양 점수',
                      style: TextStyle(fontSize: 16, color: Colors.grey),
                    ),
                    const SizedBox(height: 8),
                    if (totalScore != null)
                      Text(
                        '${totalScore!.toInt()}점',
                        style: TextStyle(
                          fontSize: 56,
                          fontWeight: FontWeight.bold,
                          color: _scoreColor,
                        ),
                      )
                    else
                      const Text(
                        '-',
                        style: TextStyle(fontSize: 56, color: Colors.grey),
                      ),
                    const SizedBox(height: 8),
                    Text(
                      _message,
                      style: const TextStyle(fontSize: 16),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 16),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        _StatItem(label: '대화 횟수', value: '$turnCount번'),
                      ],
                    ),

                    // 세부 점수 바
                    if (_hasSubScores) ...[
                      const SizedBox(height: 20),
                      const Divider(),
                      const SizedBox(height: 12),
                      const Align(
                        alignment: Alignment.centerLeft,
                        child: Text(
                          '세부 점수 (턴 평균)',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.bold,
                            color: Colors.black54,
                          ),
                        ),
                      ),
                      const SizedBox(height: 10),
                      if (totalScore != null)
                        _ResultScoreBar(label: '억양', score: totalScore!),
                      _ResultScoreBar(label: '리듬', score: rhythmScore!),
                      _ResultScoreBar(label: '강세', score: stressScore!),
                      _ResultScoreBar(label: '음색', score: mfccScore!),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: 32),

              // 다시 연습 버튼
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () {
                    Navigator.pushAndRemoveUntil(
                      context,
                      MaterialPageRoute(builder: (_) => const HomeScreen()),
                      (route) => false,
                    );
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(AppConstants.primaryColor),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: const Text(
                    '다른 연습 하기',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                ),
              ),
              const SizedBox(height: 12),

              // 같은 시나리오 다시
              SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  onPressed: () => Navigator.pop(context),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: const Text(
                    '다시 연습하기',
                    style: TextStyle(fontSize: 18),
                  ),
                ),
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}

class _StatItem extends StatelessWidget {
  final String label;
  final String value;

  const _StatItem({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
        Text(label, style: TextStyle(color: Colors.grey[600], fontSize: 13)),
      ],
    );
  }
}

class _ResultScoreBar extends StatelessWidget {
  final String label;
  final double score;

  const _ResultScoreBar({required this.label, required this.score});

  Color get _barColor {
    if (score >= 80) return Colors.green;
    if (score >= 60) return Colors.orange;
    return Colors.redAccent;
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          SizedBox(
            width: 36,
            child: Text(
              label,
              style: const TextStyle(fontSize: 13, color: Colors.black54),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: LinearProgressIndicator(
                value: score / 100,
                minHeight: 12,
                backgroundColor: Colors.grey[200],
                valueColor: AlwaysStoppedAnimation(_barColor),
              ),
            ),
          ),
          const SizedBox(width: 8),
          SizedBox(
            width: 36,
            child: Text(
              '${score.toInt()}점',
              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
              textAlign: TextAlign.right,
            ),
          ),
        ],
      ),
    );
  }
}
