import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

/// The Time Tracker mark: a stopwatch with a check, on a teal tile.
class AppLogo extends StatelessWidget {
  const AppLogo({super.key, this.size = 40});
  final double size;

  @override
  Widget build(BuildContext context) => SvgPicture.asset(
        'assets/logo.svg',
        width: size,
        height: size,
        semanticsLabel: 'Time Tracker logo',
      );
}
