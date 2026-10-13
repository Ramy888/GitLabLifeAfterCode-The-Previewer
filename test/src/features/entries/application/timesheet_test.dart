import 'package:flutter_test/flutter_test.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/application/entries_service.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/domain/entry.dart';
import 'package:starter_architecture_flutter_firebase/src/features/jobs/domain/job.dart';

Entry entry(String id, String jobId, DateTime start, int minutes) =>
    Entry(id: id, jobId: jobId, start: start, end: start.add(Duration(minutes: minutes)), comment: '');

void main() {
  const web = Job(id: 'web', name: 'Website redesign', ratePerHour: 20);
  const qa = Job(id: 'qa', name: 'Mobile app QA', ratePerHour: 10);

  test('an entry whose job was deleted shows as (deleted job) instead of throwing', () {
    final pairs = EntriesService.combine([entry('e1', 'gone', DateTime(2026, 10, 1, 9), 60)], [web]);
    expect(pairs.single.job.name, '(deleted job)');
    expect(pairs.single.job.ratePerHour, 0);
  });

  test('days come newest first, with per-day and overall totals', () {
    final sheet = EntriesService.timesheet(EntriesService.combine([
      entry('a', 'web', DateTime(2026, 10, 1, 9), 120),
      entry('b', 'qa', DateTime(2026, 10, 3, 9), 60),
      entry('c', 'web', DateTime(2026, 10, 3, 14), 30),
    ], [web, qa]));
    expect(sheet.days.map((d) => d.date.day), [3, 1]);
    expect(sheet.days.first.duration, 1.5);
    expect(sheet.days.first.pay, 20.0);
    expect(sheet.totalHours, 3.5);
    expect(sheet.totalPay, 60.0);
  });

  test('no entries gives an empty timesheet', () {
    final sheet = EntriesService.timesheet(const []);
    expect(sheet.days, isEmpty);
    expect(sheet.totalHours, 0);
  });
}
