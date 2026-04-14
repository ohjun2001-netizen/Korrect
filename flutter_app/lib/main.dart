import 'package:flutter/material.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const KorrectApp());
}

class KorrectApp extends StatelessWidget {
  const KorrectApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Korrect',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF4CAF50),
        ),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}
