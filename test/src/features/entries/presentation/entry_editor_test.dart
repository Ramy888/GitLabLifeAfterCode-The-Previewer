import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/domain/entry_times.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/presentation/entry_screen/entry_editor.dart';
import 'package:starter_architecture_flutter_firebase/src/theme/app_theme.dart';

class _Harness extends StatefulWidget {
  const _Harness({required this.initial, this.rate = 20});
  final EntryTimes initial;
  final double rate;
  @override
  State<_Harness> createState() => _HarnessState();
}

class _HarnessState extends State<_Harness> {
  late EntryTimes times = widget.initial;
  @override
  Widget build(BuildContext context) => MaterialApp(
        theme: AppTheme.light(),
        home: Scaffold(
          body: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: EntryEditor(
              times: times,
              ratePerHour: widget.rate,
              comment: '',
              onTimesChanged: (t) => setState(() => times = t),
              onCommentChanged: (_) {},
            ),
          ),
        ),
      );
}

Future<void> phone(WidgetTester tester) async {
  tester.view.physicalSize = const Size(360, 740);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
}

void main() {
  final day = DateTime(2026, 10, 13);

  testWidgets('nudges move start and duration; end and pay follow live', (tester) async {
    await phone(tester);
    await tester.pumpWidget(_Harness(initial: EntryTimes(day: day, startMinutes: 9 * 60, durationMinutes: 60)));
    expect(find.text(r'$20'), findsOneWidget);
    await tester.tap(find.byKey(EntryEditor.durationLongerKey));
    await tester.pump();
    expect(find.text('1h 15m'), findsOneWidget);
    expect(find.text(r'$25'), findsOneWidget);
    await tester.tap(find.byKey(EntryEditor.startLaterKey));
    await tester.pump();
    expect(find.text('9:15 AM'), findsOneWidget);
    expect(find.text('10:30 AM'), findsOneWidget);
  });

  testWidgets('an end past midnight says +1 day', (tester) async {
    await phone(tester);
    await tester.pumpWidget(
        _Harness(initial: EntryTimes(day: day, startMinutes: 23 * 60, durationMinutes: 120), rate: 0));
    expect(find.text('1:00 AM (+1 day)'), findsOneWidget);
    expect(find.text('Pay'), findsNothing);
  });

  testWidgets('dragging the duration slider to the far left stops at 15 minutes', (tester) async {
    await phone(tester);
    await tester.pumpWidget(_Harness(initial: EntryTimes(day: day, startMinutes: 9 * 60, durationMinutes: 240)));
    await tester.drag(find.byKey(EntryEditor.durationSliderKey), const Offset(-2000, 0));
    await tester.pump();
    expect(find.text('15m'), findsOneWidget);
    expect(tester.widget<IconButton>(find.byKey(EntryEditor.durationShorterKey)).onPressed, isNull);
  });
}
