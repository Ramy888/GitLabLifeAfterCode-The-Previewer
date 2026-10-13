import 'package:flutter_test/flutter_test.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/domain/entry_times.dart';

void main() {
  final day = DateTime(2026, 10, 13);

  test('end is start plus duration, so it can never come before the start', () {
    final t = EntryTimes(day: day, startMinutes: 9 * 60, durationMinutes: 8 * 60 + 30);
    expect(t.start, DateTime(2026, 10, 13, 9));
    expect(t.end, DateTime(2026, 10, 13, 17, 30));
    expect(t.hours, 8.5);
    expect(t.endsNextDay, isFalse);
    expect(t.end.isAfter(t.start), isTrue);
  });

  test('an end past midnight is flagged as the next day', () {
    final t = EntryTimes(day: day, startMinutes: 22 * 60, durationMinutes: 4 * 60);
    expect(t.end, DateTime(2026, 10, 14, 2));
    expect(t.endsNextDay, isTrue);
  });

  test('a new entry starts at the next quarter hour, lasting one hour', () {
    final t = EntryTimes.forNew(DateTime(2026, 10, 13, 10, 7));
    expect(t.day, day);
    expect(t.startMinutes, 10 * 60 + 15);
    expect(t.durationMinutes, 60);
  });

  test('an existing entry keeps its exact times', () {
    final t = EntryTimes.fromEntry(DateTime(2026, 10, 13, 9, 7), DateTime(2026, 10, 13, 10, 1));
    expect(t.start, DateTime(2026, 10, 13, 9, 7));
    expect(t.end, DateTime(2026, 10, 13, 10, 1));
  });

  test('a stored end before the start (old data) becomes the 15-minute minimum', () {
    final t = EntryTimes.fromEntry(DateTime(2026, 10, 13, 9), DateTime(2026, 10, 13, 8));
    expect(t.durationMinutes, 15);
  });

  test('nudges move by 15 minutes and stay in range', () {
    var t = EntryTimes(day: day, startMinutes: 0, durationMinutes: 15);
    expect(t.nudgeStart(-1).startMinutes, 0);
    expect(t.nudgeStart(1).startMinutes, 15);
    expect(t.nudgeDuration(-1).durationMinutes, 15);
    t = EntryTimes(day: day, startMinutes: 23 * 60 + 45, durationMinutes: 12 * 60);
    expect(t.nudgeStart(1).startMinutes, 23 * 60 + 45);
    expect(t.nudgeDuration(1).durationMinutes, 12 * 60);
  });

  test('a duration over 12 hours widens the slider instead of being cut', () {
    final t = EntryTimes.fromEntry(DateTime(2026, 10, 13, 8), DateTime(2026, 10, 13, 22, 10));
    expect(t.durationMinutes, 14 * 60 + 10);
    expect(t.maxDurationMinutes, 14 * 60 + 15);
    expect(EntryTimes(day: day, startMinutes: 0, durationMinutes: 60).maxDurationMinutes, 12 * 60);
  });

  test('moving the start keeps the duration; changing the day keeps both', () {
    final t = EntryTimes(day: day, startMinutes: 9 * 60, durationMinutes: 90);
    expect(t.withStart(13 * 60).end, DateTime(2026, 10, 13, 14, 30));
    final moved = t.withDay(DateTime(2026, 10, 20, 15));
    expect(moved.start, DateTime(2026, 10, 20, 9));
    expect(moved.durationMinutes, 90);
  });

  test('labels: hours and minutes', () {
    expect(EntryTimes.durationLabel(510), '8h 30m');
    expect(EntryTimes.durationLabel(60), '1h');
    expect(EntryTimes.durationLabel(45), '45m');
  });
}
