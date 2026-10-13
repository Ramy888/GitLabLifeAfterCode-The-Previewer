import 'package:flutter/material.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/domain/entry_times.dart';
import 'package:starter_architecture_flutter_firebase/src/localization/string_hardcoded.dart';
import 'package:starter_architecture_flutter_firebase/src/theme/app_theme.dart';
import 'package:starter_architecture_flutter_firebase/src/utils/format.dart';

/// The time entry form, free of Firebase: pick a day, drag a start and a duration, add a comment.
/// The end time and pay are derived, so the user never types an end that comes before the start.
class EntryEditor extends StatelessWidget {
  const EntryEditor({
    super.key,
    required this.times,
    required this.ratePerHour,
    required this.comment,
    required this.onTimesChanged,
    required this.onCommentChanged,
  });

  final EntryTimes times;
  final double ratePerHour;
  final String comment;
  final ValueChanged<EntryTimes> onTimesChanged;
  final ValueChanged<String> onCommentChanged;

  static const dayKey = Key('entry-day');
  static const startSliderKey = Key('entry-start-slider');
  static const durationSliderKey = Key('entry-duration-slider');
  static const startLaterKey = Key('entry-start-later');
  static const startEarlierKey = Key('entry-start-earlier');
  static const durationLongerKey = Key('entry-duration-longer');
  static const durationShorterKey = Key('entry-duration-shorter');

  String _clock(BuildContext context, DateTime t) => TimeOfDay.fromDateTime(t).format(context);

  Future<void> _pickDay(BuildContext context) async {
    final picked = await showDatePicker(
      context: context,
      initialDate: times.day,
      firstDate: DateTime(2015),
      lastDate: DateTime(2100),
    );
    if (picked != null) onTimesChanged(times.withDay(picked));
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = AppColors.of(context);
    final endLabel = '${_clock(context, times.end)}${times.endsNextDay ? ' (+1 day)'.hardcoded : ''}';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Card(
          child: ListTile(
            key: dayKey,
            leading: const Icon(Icons.calendar_today_outlined),
            title: Text('Day'.hardcoded),
            subtitle: Text('${Format.dayOfWeek(times.day)}, ${Format.date(times.day)}'),
            trailing: const Icon(Icons.edit_calendar_outlined),
            onTap: () => _pickDay(context),
          ),
        ),
        const SizedBox(height: 12),
        _SliderCard(
          icon: Icons.play_circle_outline,
          label: 'Start'.hardcoded,
          readout: _clock(context, times.start),
          sliderKey: startSliderKey,
          earlierKey: startEarlierKey,
          laterKey: startLaterKey,
          value: times.startMinutes,
          min: 0,
          max: times.maxStartMinutes,
          onChanged: (m) => onTimesChanged(times.withStart(m)),
          onNudge: (d) => onTimesChanged(times.nudgeStart(d)),
        ),
        const SizedBox(height: 12),
        _SliderCard(
          icon: Icons.timelapse_outlined,
          label: 'Duration'.hardcoded,
          readout: EntryTimes.durationLabel(times.durationMinutes),
          sliderKey: durationSliderKey,
          earlierKey: durationShorterKey,
          laterKey: durationLongerKey,
          value: times.durationMinutes,
          min: times.minDurationMinutes,
          max: times.maxDurationMinutes,
          onChanged: (m) => onTimesChanged(times.withDuration(m)),
          onNudge: (d) => onTimesChanged(times.nudgeDuration(d)),
        ),
        const SizedBox(height: 12),
        Card(
          color: colors.headerFill,
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Wrap(
              alignment: WrapAlignment.spaceBetween,
              runSpacing: 8,
              spacing: 16,
              children: [
                _Fact(label: 'Ends'.hardcoded, value: endLabel),
                _Fact(label: 'Hours'.hardcoded, value: Format.hours(times.hours)),
                if (ratePerHour > 0)
                  _Fact(
                    label: 'Pay'.hardcoded,
                    value: Format.currency(ratePerHour * times.hours),
                    color: colors.pay,
                  ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        TextFormField(
          initialValue: comment,
          maxLength: 50,
          decoration: InputDecoration(
            labelText: 'Comment'.hardcoded,
            hintText: 'What did you work on?'.hardcoded,
            prefixIcon: const Icon(Icons.notes_outlined),
          ),
          style: theme.textTheme.bodyLarge,
          onChanged: onCommentChanged,
        ),
      ],
    );
  }
}

class _SliderCard extends StatelessWidget {
  const _SliderCard({
    required this.icon,
    required this.label,
    required this.readout,
    required this.sliderKey,
    required this.earlierKey,
    required this.laterKey,
    required this.value,
    required this.min,
    required this.max,
    required this.onChanged,
    required this.onNudge,
  });

  final IconData icon;
  final String label;
  final String readout;
  final Key sliderKey;
  final Key earlierKey;
  final Key laterKey;
  final int value;
  final int min;
  final int max;
  final ValueChanged<int> onChanged;
  final ValueChanged<int> onNudge;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 8, 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Icon(icon, color: theme.colorScheme.primary),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(label, style: theme.textTheme.titleMedium, overflow: TextOverflow.ellipsis),
                ),
                Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: Text(
                    readout,
                    style: theme.textTheme.headlineSmall!.copyWith(fontWeight: FontWeight.w700),
                  ),
                ),
              ],
            ),
            Row(
              children: [
                IconButton.filledTonal(
                  key: earlierKey,
                  tooltip: '15 minutes less'.hardcoded,
                  onPressed: value > min ? () => onNudge(-1) : null,
                  icon: const Icon(Icons.remove),
                ),
                Expanded(
                  child: Slider(
                    key: sliderKey,
                    // An existing off-grid time (after 23:45, or under 15 minutes) sits at the end until moved.
                    value: value.clamp(min, max).toDouble(),
                    min: min.toDouble(),
                    max: max.toDouble(),
                    divisions: (max - min) ~/ EntryTimes.step > 0 ? (max - min) ~/ EntryTimes.step : null,
                    label: readout,
                    semanticFormatterCallback: (_) => readout,
                    onChanged: (v) => onChanged(v.round()),
                  ),
                ),
                IconButton.filledTonal(
                  key: laterKey,
                  tooltip: '15 minutes more'.hardcoded,
                  onPressed: value < max ? () => onNudge(1) : null,
                  icon: const Icon(Icons.add),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _Fact extends StatelessWidget {
  const _Fact({required this.label, required this.value, this.color});
  final String label;
  final String value;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: theme.textTheme.labelMedium!.copyWith(color: AppColors.of(context).muted)),
        Text(value, style: theme.textTheme.titleLarge!.copyWith(color: color, fontWeight: FontWeight.w700)),
      ],
    );
  }
}
