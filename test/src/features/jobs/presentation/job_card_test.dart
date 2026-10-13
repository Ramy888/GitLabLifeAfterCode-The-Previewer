import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:starter_architecture_flutter_firebase/src/features/jobs/domain/job.dart';
import 'package:starter_architecture_flutter_firebase/src/features/jobs/presentation/jobs_screen/job_card.dart';
import 'package:starter_architecture_flutter_firebase/src/theme/app_theme.dart';

Widget host(Widget child) => MaterialApp(theme: AppTheme.light(), home: Scaffold(body: child));

void main() {
  testWidgets('a paid job shows its decimal rate, an unpaid job says so', (tester) async {
    await tester.pumpWidget(host(const Column(children: [
      JobCard(job: Job(id: 'a', name: 'Website redesign', ratePerHour: 12.5)),
      JobCard(job: Job(id: 'b', name: 'volunteering', ratePerHour: 0)),
    ])));
    expect(find.textContaining('12.50 / hour'), findsOneWidget);
    expect(find.text('Unpaid'), findsOneWidget);
    expect(find.text('V'), findsOneWidget); // initial avatar
  });

  testWidgets('deleting a job asks first and names what goes with it', (tester) async {
    bool? result;
    await tester.pumpWidget(host(Builder(
      builder: (context) => TextButton(
        onPressed: () async =>
            result = await confirmJobDelete(context, const Job(id: 'a', name: 'QA', ratePerHour: 1)),
        child: const Text('go'),
      ),
    )));
    await tester.tap(find.text('go'));
    await tester.pumpAndSettle();
    expect(find.text('Delete "QA"?'), findsOneWidget);
    expect(find.textContaining('every time entry'), findsOneWidget);
    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();
    expect(result, isFalse);
  });

  testWidgets('the empty state explains what a job is and offers New job', (tester) async {
    var added = 0;
    await tester.pumpWidget(host(JobsEmptyState(onAdd: () => added++)));
    expect(find.textContaining('A job is anything you track time for'), findsOneWidget);
    await tester.tap(find.text('New job'));
    expect(added, 1);
  });
}
