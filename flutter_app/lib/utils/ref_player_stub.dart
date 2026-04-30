import 'package:audioplayers/audioplayers.dart';

class RefPlayer {
  AudioPlayer? _player;

  Future<void> play(String url) async {
    if (_player == null) {
      _player = AudioPlayer();
    }
    await _player!.play(UrlSource(url));
  }

  Future<void> stop() async {
    await _player?.stop();
  }

  void dispose() {
    _player?.dispose();
    _player = null;
  }
}
