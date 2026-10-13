import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:starter_architecture_flutter_firebase/src/features/authentication/presentation/account_body.dart';
import 'package:starter_architecture_flutter_firebase/src/features/authentication/presentation/sign_in_header.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/application/entries_service.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/domain/entry.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/domain/entry_times.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/domain/timesheet.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/presentation/entries_screen.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/presentation/entry_screen/entry_editor.dart';
import 'package:starter_architecture_flutter_firebase/src/features/jobs/domain/job.dart';
import 'package:starter_architecture_flutter_firebase/src/features/jobs/presentation/job_entries_screen/entry_list_item.dart';
import 'package:starter_architecture_flutter_firebase/src/features/jobs/presentation/jobs_screen/job_card.dart';
import 'package:starter_architecture_flutter_firebase/src/routing/scaffold_with_nested_navigation.dart';
import 'package:starter_architecture_flutter_firebase/src/theme/app_theme.dart';

/// R8: every plain widget at phone, tablet and laptop sizes, light and dark. A RenderFlex overflow fails the test.
const sizes = {
  'small phone': Size(360, 740),
  'phone': Size(390, 844),
  'tablet portrait': Size(820, 1180),
  'tablet landscape': Size(1180, 820),
  'laptop': Size(1440, 900),
};

const longJob = Job(id: 'j', name: 'Quarterly accessibility audit for the client portal', ratePerHour: 1250.75);
final day = DateTime(2026, 10, 13);
Entry entry(String jobId, int hour, int minutes) => Entry(
    id: '$jobId$hour', jobId: jobId, start: day.add(Duration(hours: hour)),
    end: day.add(Duration(hours: hour, minutes: minutes)), comment: 'Reviewed the sign-up flow with the team');

final Timesheet sheet = EntriesService.timesheet(EntriesService.combine(
  [entry('j', 9, 450), entry('q', 14, 135), entry('gone', 18, 60)],
  [longJob, const Job(id: 'q', name: 'Mobile app QA', ratePerHour: 10)],
));

final screens = <String, Widget Function()>{
  'jobs': () => ListView(padding: const EdgeInsets.all(16), children: const [
        JobCard(job: longJob),
        JobCard(job: Job(id: 'b', name: 'Volunteering', ratePerHour: 0)),
      ]),
  'jobs empty': () => JobsEmptyState(onAdd: () {}),
  'job entries': () => ListView(padding: const EdgeInsets.all(16), children: [
        EntryListItem(entry: entry('j', 9, 450), job: longJob),
      ]),
  'timesheet': () => TimesheetView(sheet: sheet),
  'timesheet empty': () => const TimesheetView(sheet: Timesheet(days: [], totalHours: 0, totalPay: 0)),
  'entry editor': () => SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: EntryEditor(
          times: EntryTimes(day: day, startMinutes: 23 * 60 + 45, durationMinutes: 11 * 60 + 45),
          ratePerHour: 1250.75,
          comment: '',
          onTimesChanged: (_) {},
          onCommentChanged: (_) {},
        ),
      ),
  'account': () => AccountBody(
        avatar: const CircleAvatar(radius: 48),
        name: const Text('A rather long display name for layout'),
        email: 'someone.with.a.long.address@example.com',
        isAnonymous: false,
        onSignOut: () {},
        deleteButton: OutlinedButton(onPressed: () {}, child: const Text('Delete account')),
        version: '2.2.0',
      ),
  'sign-in header': () => const Center(child: SignInHeader()),
  'sign-in side panel': () => const SingleChildScrollView(child: SignInHeader(showPoints: true)),
  'nav bar': () => ScaffoldWithNavigationBar(body: const SizedBox(), currentIndex: 1, onDestinationSelected: (_) {}),
  'nav rail': () => ScaffoldWithNavigationRail(body: const SizedBox(), currentIndex: 2, onDestinationSelected: (_) {}),
};

void main() {
  for (final brightness in Brightness.values) {
    for (final size in sizes.entries) {
      for (final screen in screens.entries) {
        testWidgets('${screen.key} at ${size.key} (${brightness.name})', (tester) async {
          tester.view.physicalSize = size.value;
          tester.view.devicePixelRatio = 1;
          addTearDown(tester.view.reset);
          await tester.pumpWidget(MaterialApp(
            theme: brightness == Brightness.light ? AppTheme.light() : AppTheme.dark(),
            home: Scaffold(body: screen.value()),
          ));
          await tester.pump();
          expect(tester.takeException(), isNull);
        });
      }
    }
  }
}
