import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

/// R1: screens take colours from the theme. Only lib/src/theme/ may name a `Colors.` constant
/// (`Colors.transparent` is allowed anywhere). Generated files and firebase_options.dart are skipped.
String _stripComments(String source) => source
    .replaceAll(RegExp(r'/\*[\s\S]*?\*/'), '')
    .replaceAll(RegExp(r'//[^\n]*'), '');

void main() {
  test('no hard-coded Colors outside the theme', () {
    final offenders = <String>[];
    final files = Directory('lib/src')
        .listSync(recursive: true)
        .whereType<File>()
        .where((f) => f.path.endsWith('.dart'))
        .where((f) => !f.path.endsWith('.g.dart'))
        .where((f) => !f.path.contains('/theme/'))
        .where((f) => !f.path.endsWith('firebase_options.dart'));
    for (final file in files) {
      final code = _stripComments(file.readAsStringSync());
      for (final m in RegExp(r'\bColors\.(\w+)').allMatches(code)) {
        if (m.group(1) != 'transparent') offenders.add('${file.path}: ${m.group(0)}');
      }
    }
    expect(offenders, isEmpty);
  });
}
