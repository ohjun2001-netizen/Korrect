class Scenario {
  final String id;
  final String title;
  final String description;

  Scenario({
    required this.id,
    required this.title,
    required this.description,
  });

  factory Scenario.fromJson(Map<String, dynamic> json) {
    return Scenario(
      id: json['id'] as String,
      title: json['title'] as String,
      description: json['description'] as String? ?? '',
    );
  }
}

class ScenarioTurn {
  final int index;
  final String speaker;
  final String text;
  final String? expectedUserReply;
  final String? hint;

  ScenarioTurn({
    required this.index,
    required this.speaker,
    required this.text,
    this.expectedUserReply,
    this.hint,
  });

  factory ScenarioTurn.fromJson(Map<String, dynamic> json) {
    return ScenarioTurn(
      index: json['index'] as int,
      speaker: json['speaker'] as String,
      text: json['text'] as String,
      expectedUserReply: json['expected_user_reply'] as String?,
      hint: json['hint'] as String?,
    );
  }
}
