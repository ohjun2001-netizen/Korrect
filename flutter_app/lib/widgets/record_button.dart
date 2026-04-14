import 'package:flutter/material.dart';

class RecordButton extends StatelessWidget {
  final bool isRecording;
  final bool isLoading;
  final VoidCallback onTap;

  const RecordButton({
    super.key,
    required this.isRecording,
    required this.isLoading,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return Container(
        width: 80,
        height: 80,
        decoration: const BoxDecoration(
          color: Colors.grey,
          shape: BoxShape.circle,
        ),
        child: const Center(
          child: CircularProgressIndicator(color: Colors.white),
        ),
      );
    }

    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        width: isRecording ? 90 : 80,
        height: isRecording ? 90 : 80,
        decoration: BoxDecoration(
          color: isRecording ? Colors.red : const Color(0xFF4CAF50),
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: (isRecording ? Colors.red : const Color(0xFF4CAF50))
                  .withOpacity(0.4),
              blurRadius: isRecording ? 20 : 10,
              spreadRadius: isRecording ? 5 : 2,
            ),
          ],
        ),
        child: Icon(
          isRecording ? Icons.stop : Icons.mic,
          color: Colors.white,
          size: 36,
        ),
      ),
    );
  }
}
