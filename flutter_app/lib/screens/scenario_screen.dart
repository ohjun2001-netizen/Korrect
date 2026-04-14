import 'dart:io';
import 'package:flutter/material.dart';
import '../constants.dart';
import '../models/scenario_model.dart';
import '../models/process_result.dart';
import '../services/api_service.dart';
import '../services/audio_service.dart';
import '../widgets/record_button.dart';
import '../widgets/pitch_chart.dart';
import 'result_screen.dart';

class ScenarioScreen extends StatefulWidget {
  final Scenario scenario;

  const ScenarioScreen({super.key, required this.scenario});

  @override
  State<ScenarioScreen> createState() => _ScenarioScreenState();
}

class _ScenarioScreenState extends State<ScenarioScreen> {
  final List<_ChatMessage> _messages = [];
  final List<Map<String, String>> _history = [];
  final ScrollController _scrollController = ScrollController();

  bool _isRecording = false;
  bool _isLoading = false;
  int _turnIndex = 0;
  double _totalScore = 0;
  int _scoreCount = 0;

  static const int _maxTurns = 5;

  @override
  void initState() {
    super.initState();
    _loadOpeningMessage();
  }

  @override
  void dispose() {
    AudioService.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _loadOpeningMessage() async {
    setState(() => _isLoading = true);
    try {
      final data = await ApiService.getOpeningMessage(widget.scenario.id);
      final reply = data['reply'] as String;
      final hint = data['hint'] as String?;
      setState(() {
        _messages.add(_ChatMessage(
          text: reply,
          isAi: true,
          hint: hint,
        ));
        _history.add({'role': 'model', 'text': reply});
        _isLoading = false;
      });
      _scrollToBottom();
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _toggleRecording() async {
    if (_isRecording) {
      await _stopAndProcess();
    } else {
      await _startRecording();
    }
  }

  Future<void> _startRecording() async {
    final hasPermission = await AudioService.hasPermission();
    if (!hasPermission) {
      _showSnackBar('마이크 권한이 필요해요!');
      return;
    }
    await AudioService.startRecording();
    setState(() => _isRecording = true);
  }

  Future<void> _stopAndProcess() async {
    setState(() {
      _isRecording = false;
      _isLoading = true;
    });

    final audioFile = await AudioService.stopRecording();
    if (audioFile == null) {
      setState(() => _isLoading = false);
      _showSnackBar('녹음 파일을 찾을 수 없어요.');
      return;
    }

    try {
      final result = await ApiService.processTurn(
        scenarioId: widget.scenario.id,
        audioFile: audioFile,
        history: List.from(_history),
        turnIndex: _turnIndex,
      );

      _handleResult(result);
    } catch (e) {
      _showSnackBar('처리 중 오류가 발생했어요: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _handleResult(ProcessResult result) {
    // 사용자 발화 추가
    setState(() {
      _messages.add(_ChatMessage(
        text: result.stt.text.isEmpty ? '(알아듣지 못했어요)' : result.stt.text,
        isAi: false,
        prosody: result.prosody,
        score: result.totalScore,
      ));
    });

    // 점수 누적
    if (result.totalScore != null) {
      _totalScore += result.totalScore!;
      _scoreCount++;
    }

    // 히스토리 업데이트
    _history.add({'role': 'user', 'text': result.stt.text});

    // AI 답변 추가
    setState(() {
      _messages.add(_ChatMessage(
        text: result.chat.reply,
        isAi: true,
        hint: result.chat.hint,
      ));
      _history.add({'role': 'model', 'text': result.chat.reply});
      _turnIndex++;
    });

    _scrollToBottom();

    // 최대 턴 도달 시 결과 화면으로
    if (_turnIndex >= _maxTurns) {
      Future.delayed(const Duration(milliseconds: 800), () {
        final avgScore = _scoreCount > 0 ? _totalScore / _scoreCount : null;
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => ResultScreen(
              scenario: widget.scenario,
              totalScore: avgScore,
              turnCount: _turnIndex,
            ),
          ),
        );
      });
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _showSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final emoji = AppConstants.scenarioEmoji[widget.scenario.id] ?? '💬';

    return Scaffold(
      backgroundColor: const Color(AppConstants.bgColor),
      appBar: AppBar(
        backgroundColor: const Color(AppConstants.primaryColor),
        title: Text(
          '$emoji ${widget.scenario.title}',
          style: const TextStyle(color: Colors.white),
        ),
        iconTheme: const IconThemeData(color: Colors.white),
        actions: [
          Center(
            child: Padding(
              padding: const EdgeInsets.only(right: 16),
              child: Text(
                '$_turnIndex/$_maxTurns',
                style: const TextStyle(color: Colors.white70),
              ),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // 대화 목록
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                return _MessageBubble(message: _messages[index]);
              },
            ),
          ),

          // 로딩 표시
          if (_isLoading)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                  SizedBox(width: 8),
                  Text('처리 중...', style: TextStyle(color: Colors.grey)),
                ],
              ),
            ),

          // 녹음 버튼
          Container(
            padding: const EdgeInsets.symmetric(vertical: 24),
            color: Colors.white,
            child: Column(
              children: [
                if (_isRecording)
                  const Padding(
                    padding: EdgeInsets.only(bottom: 8),
                    child: Text(
                      '말하고 있어요... 버튼을 눌러서 멈춰요',
                      style: TextStyle(color: Colors.red, fontSize: 13),
                    ),
                  )
                else
                  const Padding(
                    padding: EdgeInsets.only(bottom: 8),
                    child: Text(
                      '버튼을 눌러서 말해봐요!',
                      style: TextStyle(color: Colors.grey, fontSize: 13),
                    ),
                  ),
                RecordButton(
                  isRecording: _isRecording,
                  isLoading: _isLoading,
                  onTap: _isLoading ? () {} : _toggleRecording,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// 메시지 데이터 모델
class _ChatMessage {
  final String text;
  final bool isAi;
  final String? hint;
  final ProsodyResult? prosody;
  final double? score;

  _ChatMessage({
    required this.text,
    required this.isAi,
    this.hint,
    this.prosody,
    this.score,
  });
}

// 말풍선 위젯
class _MessageBubble extends StatefulWidget {
  final _ChatMessage message;

  const _MessageBubble({required this.message});

  @override
  State<_MessageBubble> createState() => _MessageBubbleState();
}

class _MessageBubbleState extends State<_MessageBubble> {
  bool _showPitch = false;

  @override
  Widget build(BuildContext context) {
    final isAi = widget.message.isAi;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        crossAxisAlignment:
            isAi ? CrossAxisAlignment.start : CrossAxisAlignment.end,
        children: [
          Row(
            mainAxisAlignment:
                isAi ? MainAxisAlignment.start : MainAxisAlignment.end,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              if (isAi) ...[
                const CircleAvatar(
                  radius: 16,
                  backgroundColor: Color(0xFF4CAF50),
                  child: Text('AI', style: TextStyle(color: Colors.white, fontSize: 10)),
                ),
                const SizedBox(width: 8),
              ],
              Flexible(
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 14,
                    vertical: 10,
                  ),
                  decoration: BoxDecoration(
                    color: isAi ? Colors.white : const Color(0xFF4CAF50),
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.05),
                        blurRadius: 5,
                      ),
                    ],
                  ),
                  child: Text(
                    widget.message.text,
                    style: TextStyle(
                      color: isAi ? Colors.black87 : Colors.white,
                      fontSize: 15,
                    ),
                  ),
                ),
              ),
              // 점수 표시 (사용자 발화에만)
              if (!isAi && widget.message.score != null) ...[
                const SizedBox(width: 8),
                _ScoreBadge(score: widget.message.score!),
              ],
            ],
          ),

          // 힌트 표시 (AI 메시지에만)
          if (isAi && widget.message.hint != null)
            Padding(
              padding: const EdgeInsets.only(left: 40, top: 4),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: Colors.amber[50],
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.amber.shade300),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text('💡 ', style: TextStyle(fontSize: 12)),
                    Text(
                      '"${widget.message.hint}"',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.amber[900],
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                  ],
                ),
              ),
            ),

          // 피치 그래프 토글 (사용자 발화 + 피치 데이터 있을 때)
          if (!isAi && widget.message.prosody != null) ...[
            const SizedBox(height: 4),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                onPressed: () => setState(() => _showPitch = !_showPitch),
                icon: Icon(
                  _showPitch ? Icons.expand_less : Icons.show_chart,
                  size: 16,
                ),
                label: Text(
                  _showPitch ? '그래프 닫기' : '억양 그래프 보기',
                  style: const TextStyle(fontSize: 12),
                ),
                style: TextButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  minimumSize: Size.zero,
                ),
              ),
            ),
            if (_showPitch)
              Container(
                margin: const EdgeInsets.only(top: 4),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.05),
                      blurRadius: 5,
                    ),
                  ],
                ),
                child: PitchChart(
                  userPitch: widget.message.prosody!.pitchContour,
                  refPitch: widget.message.prosody!.refPitchContour,
                ),
              ),
          ],
        ],
      ),
    );
  }
}

class _ScoreBadge extends StatelessWidget {
  final double score;

  const _ScoreBadge({required this.score});

  Color get _color {
    if (score >= 80) return Colors.green;
    if (score >= 60) return Colors.orange;
    return Colors.red;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: _color,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        '${score.toInt()}점',
        style: const TextStyle(
          color: Colors.white,
          fontSize: 12,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}
