import 'dart:html' as html;

class RefPlayer {
  html.AudioElement? _audio;

  Future<void> play(String url) async {
    _audio?.pause();
    _audio = html.AudioElement(url);
    _audio!.play();
  }

  Future<void> stop() async {
    _audio?.pause();
    _audio = null;
  }

  void dispose() {
    _audio?.pause();
    _audio = null;
  }
}
