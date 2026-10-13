import 'package:flutter/foundation.dart';

/// The times the entry editor edits: a day, a start (minutes after midnight) and a duration in minutes.
/// The end is always start + duration, so an entry can't end before it starts.
@immutable
class EntryTimes {
  const EntryTimes({required this.day, required this.startMinutes, required this.durationMinutes});

  /// Slider and nudge step.
  static const step = 15;

  /// Default top of the duration slider; a longer existing entry widens it (see [maxDurationMinutes]).
  static const maxDefaultDuration = 12 * 60;

  /// Last start the slider offers: 23:45.
  static const lastStart = 24 * 60 - step;

  final DateTime day;
  final int startMinutes;
  final int durationMinutes;

  /// A new entry: today, from the next quarter hour, for one hour.
  factory EntryTimes.forNew(DateTime now) {
    final minutes = now.hour * 60 + now.minute;
    final rounded = ((minutes + step - 1) ~/ step) * step;
    return EntryTimes(day: _dateOnly(now), startMinutes: rounded.clamp(0, lastStart), durationMinutes: 60);
  }

  /// An existing entry, kept to the minute until a slider moves. A stored end before the start (from before the
  /// editor prevented it) becomes the shortest duration.
  factory EntryTimes.fromEntry(DateTime start, DateTime end) {
    final duration = end.difference(start).inMinutes;
    return EntryTimes(
      day: _dateOnly(start),
      startMinutes: start.hour * 60 + start.minute,
      durationMinutes: duration < step ? step : duration,
    );
  }

  DateTime get start => DateTime(day.year, day.month, day.day, 0, startMinutes);
  DateTime get end => start.add(Duration(minutes: durationMinutes));
  bool get endsNextDay => _dateOnly(end).isAfter(day);
  double get hours => durationMinutes / 60.0;

  /// Top of the start slider: 23:45, or later if an existing entry starts later.
  int get maxStartMinutes => startMinutes > lastStart ? startMinutes : lastStart;

  /// Top of the duration slider: 12 hours, or the existing duration rounded up to a step.
  int get maxDurationMinutes {
    final rounded = ((durationMinutes + step - 1) ~/ step) * step;
    return rounded > maxDefaultDuration ? rounded : maxDefaultDuration;
  }

  /// Bottom of the duration slider: one step, or less if an existing entry is shorter.
  int get minDurationMinutes => durationMinutes < step ? durationMinutes : step;

  EntryTimes withDay(DateTime newDay) =>
      EntryTimes(day: _dateOnly(newDay), startMinutes: startMinutes, durationMinutes: durationMinutes);
  EntryTimes withStart(int minutes) =>
      EntryTimes(day: day, startMinutes: minutes.clamp(0, maxStartMinutes), durationMinutes: durationMinutes);
  EntryTimes withDuration(int minutes) => EntryTimes(
      day: day, startMinutes: startMinutes, durationMinutes: minutes.clamp(minDurationMinutes, maxDurationMinutes));

  /// One step earlier (-1) or later (+1), snapping an off-grid time to the grid first.
  EntryTimes nudgeStart(int direction) => withStart(_snap(startMinutes, direction));
  EntryTimes nudgeDuration(int direction) => withDuration(_snap(durationMinutes, direction));

  static int _snap(int value, int direction) {
    final onGrid = value % step == 0;
    if (direction > 0) return onGrid ? value + step : ((value ~/ step) + 1) * step;
    return onGrid ? value - step : (value ~/ step) * step;
  }

  static String durationLabel(int minutes) {
    final h = minutes ~/ 60;
    final m = minutes % 60;
    if (h == 0) return '${m}m';
    if (m == 0) return '${h}h';
    return '${h}h ${m}m';
  }

  static DateTime _dateOnly(DateTime t) => DateTime(t.year, t.month, t.day);

  @override
  bool operator ==(Object other) =>
      other is EntryTimes &&
      other.day == day &&
      other.startMinutes == startMinutes &&
      other.durationMinutes == durationMinutes;

  @override
  int get hashCode => Object.hash(day, startMinutes, durationMinutes);
}
