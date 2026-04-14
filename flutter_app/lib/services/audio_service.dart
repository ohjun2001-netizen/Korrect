import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

class AudioService {
  static final AudioRecorder _recorder = AudioRecorder();

  static Future<bool> hasPermission() async {
    return await _recorder.hasPermission();
  }

  static Future<void> startRecording() async {
    final dir = await getTemporaryDirectory();
    final path = '${dir.path}/korrect_recording.wav';

    await _recorder.start(
      const RecordConfig(
        encoder: AudioEncoder.wav,
        sampleRate: 16000,
        numChannels: 1,
        bitRate: 256000,
      ),
      path: path,
    );
  }

  static Future<File?> stopRecording() async {
    final path = await _recorder.stop();
    if (path == null) return null;
    return File(path);
  }

  static Future<bool> isRecording() async {
    return await _recorder.isRecording();
  }

  static Future<void> dispose() async {
    await _recorder.dispose();
  }
}
