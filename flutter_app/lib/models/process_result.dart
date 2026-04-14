class STTResult {
  final String text;
  final String language;

  STTResult({required this.text, required this.language});

  factory STTResult.fromJson(Map<String, dynamic> json) {
    return STTResult(
      text: json['text'] as String,
      language: json['language'] as String,
    );
  }
}

class ProsodyResult {
  final List<double> pitchContour;
  final List<double> refPitchContour;
  final double score;
  final double dtwDistance;

  ProsodyResult({
    required this.pitchContour,
    required this.refPitchContour,
    required this.score,
    required this.dtwDistance,
  });

  factory ProsodyResult.fromJson(Map<String, dynamic> json) {
    return ProsodyResult(
      pitchContour: (json['pitch_contour'] as List)
          .map((e) => (e as num).toDouble())
          .toList(),
      refPitchContour: (json['ref_pitch_contour'] as List)
          .map((e) => (e as num).toDouble())
          .toList(),
      score: (json['score'] as num).toDouble(),
      dtwDistance: (json['dtw_distance'] as num).toDouble(),
    );
  }
}

class ChatResult {
  final String reply;
  final String? hint;

  ChatResult({required this.reply, this.hint});

  factory ChatResult.fromJson(Map<String, dynamic> json) {
    return ChatResult(
      reply: json['reply'] as String,
      hint: json['hint'] as String?,
    );
  }
}

class ProcessResult {
  final STTResult stt;
  final ProsodyResult? prosody;
  final ChatResult chat;
  final double? totalScore;

  ProcessResult({
    required this.stt,
    this.prosody,
    required this.chat,
    this.totalScore,
  });

  factory ProcessResult.fromJson(Map<String, dynamic> json) {
    return ProcessResult(
      stt: STTResult.fromJson(json['stt'] as Map<String, dynamic>),
      prosody: json['prosody'] != null
          ? ProsodyResult.fromJson(json['prosody'] as Map<String, dynamic>)
          : null,
      chat: ChatResult.fromJson(json['chat'] as Map<String, dynamic>),
      totalScore: json['total_score'] != null
          ? (json['total_score'] as num).toDouble()
          : null,
    );
  }
}
