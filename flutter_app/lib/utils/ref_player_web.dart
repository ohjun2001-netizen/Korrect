import 'dart:async';
import 'dart:html' as html;

class RefPlayer {
  html.AudioElement? _audio;
  final StreamController<Duration> _positionController =
      StreamController<Duration>.broadcast();
  final StreamController<Duration> _durationController =
      StreamController<Duration>.broadcast();
  final StreamController<void> _completeController =
      StreamController<void>.broadcast();

  Stream<Duration> get positionStream => _positionController.stream;
  Stream<Duration> get durationStream => _durationController.stream;
  Stream<void> get onComplete => _completeController.stream;

  Future<void> play(String url) async {
    _audio?.pause();
    final audio = html.AudioElement(url);
    _audio = audio;

    audio.onLoadedMetadata.listen((_) {
      final dur = audio.duration;
      if (!dur.isNaN && !dur.isInfinite) {
        _durationController.add(Duration(milliseconds: (dur * 1000).round()));
      }
    });
    audio.onTimeUpdate.listen((_) {
      _positionController.add(
          Duration(milliseconds: (audio.currentTime * 1000).round()));
    });
    audio.onEnded.listen((_) {
      _completeController.add(null);
    });

    await audio.play();
  }

  Future<void> stop() async {
    _audio?.pause();
    _audio = null;
  }

  void dispose() {
    _audio?.pause();
    _audio = null;
    _positionController.close();
    _durationController.close();
    _completeController.close();
  }
}
