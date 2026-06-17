import 'dart:math';
import 'package:flutter/material.dart';

class MatrixRainBackground extends StatefulWidget {
  final double opacity;
  const MatrixRainBackground({super.key, this.opacity = 0.15});

  @override
  State<MatrixRainBackground> createState() => _MatrixRainBackgroundState();
}

class _MatrixRainBackgroundState extends State<MatrixRainBackground> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  List<RainLine>? _rainLines;
  final Random _random = Random();
  double _lastWidth = 0.0;
  double _lastHeight = 0.0;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 10),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _initRainLines(double width, double height) {
    const double fontSize = 14.0;
    final int columnCount = (width / fontSize).floor() + 1;
    _rainLines = List.generate(columnCount, (index) {
      return RainLine(
        x: index * fontSize,
        y: _random.nextDouble() * -height,
        speed: 2.0 + _random.nextDouble() * 4.0,
        chars: List.generate(15 + _random.nextInt(15), (_) => _getRandomChar()),
        fontSize: fontSize,
      );
    });
    _lastWidth = width;
    _lastHeight = height;
  }

  String _getRandomChar() {
    // Random characters (katakana, uppercase letters, numbers)
    const String chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ";
    return chars[_random.nextInt(chars.length)];
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final width = constraints.maxWidth;
        final height = constraints.maxHeight;

        if (_rainLines == null || width != _lastWidth || height != _lastHeight) {
          _initRainLines(width, height);
        }

        return AnimatedBuilder(
          animation: _controller,
          builder: (context, child) {
            // Update rain positions
            if (_rainLines != null) {
              for (var line in _rainLines!) {
                line.y += line.speed;
                // If the drop is completely off-screen, reset it to the top
                if (line.y - (line.chars.length * line.fontSize) > height) {
                  line.y = -_random.nextDouble() * 100.0;
                  line.speed = 2.0 + _random.nextDouble() * 4.0;
                  line.chars = List.generate(15 + _random.nextInt(15), (_) => _getRandomChar());
                }
                // Randomly change a character in the trail to create a dynamic effect
                if (_random.nextDouble() < 0.05) {
                  line.chars[_random.nextInt(line.chars.length)] = _getRandomChar();
                }
              }
            }

            return CustomPaint(
              painter: MatrixRainPainter(
                rainLines: _rainLines ?? [],
                opacity: widget.opacity,
              ),
              size: Size(width, height),
            );
          },
        );
      },
    );
  }
}

class RainLine {
  final double x;
  double y;
  double speed;
  List<String> chars;
  final double fontSize;

  RainLine({
    required this.x,
    required this.y,
    required this.speed,
    required this.chars,
    required this.fontSize,
  });
}

class MatrixRainPainter extends CustomPainter {
  final List<RainLine> rainLines;
  final double opacity;

  MatrixRainPainter({required this.rainLines, required this.opacity});

  @override
  void paint(Canvas canvas, Size size) {
    final textPainter = TextPainter(
      textDirection: TextDirection.ltr,
    );

    for (var line in rainLines) {
      for (int i = 0; i < line.chars.length; i++) {
        final double charY = line.y - (i * line.fontSize);
        if (charY < -line.fontSize || charY > size.height) {
          continue;
        }

        // Head character is bright white-green, tail fades out
        Color charColor;
        if (i == 0) {
          charColor = Colors.white.withOpacity(opacity);
        } else {
          final double ageFactor = 1.0 - (i / line.chars.length);
          charColor = const Color(0xFF00FF41).withOpacity(ageFactor * opacity);
        }

        textPainter.text = TextSpan(
          text: line.chars[i],
          style: TextStyle(
            color: charColor,
            fontSize: line.fontSize,
            fontFamily: 'monospace',
            fontWeight: i == 0 ? FontWeight.bold : FontWeight.normal,
          ),
        );

        textPainter.layout();
        textPainter.paint(canvas, Offset(line.x, charY));
      }
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
