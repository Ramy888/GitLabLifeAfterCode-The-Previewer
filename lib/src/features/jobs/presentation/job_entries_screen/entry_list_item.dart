import 'package:starter_architecture_flutter_firebase/src/common_widgets/delete_swipe_background.dart';
import 'package:flutter/material.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/domain/entry.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/domain/entry_times.dart';
import 'package:starter_architecture_flutter_firebase/src/features/jobs/domain/job.dart';
import 'package:starter_architecture_flutter_firebase/src/theme/app_theme.dart';
import 'package:starter_architecture_flutter_firebase/src/utils/format.dart';

/// One time entry of a job: day, start to end, duration, pay and comment.
class EntryListItem extends StatelessWidget {
  const EntryListItem({super.key, required this.entry, required this.job, this.onTap});

  final Entry entry;
  final Job job;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = AppColors.of(context);
    final startTime = TimeOfDay.fromDateTime(entry.start).format(context);
    final endTime = TimeOfDay.fromDateTime(entry.end).format(context);
    final minutes = entry.end.difference(entry.start).inMinutes;
    final pay = job.ratePerHour * entry.durationInHours;
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 52,
                padding: const EdgeInsets.symmetric(vertical: 6),
                decoration: BoxDecoration(
                  color: colors.headerFill,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Column(
                  children: [
                    Text(Format.dayOfWeek(entry.start), style: theme.textTheme.labelMedium),
                    Text('${entry.start.day}',
                        style: theme.textTheme.titleLarge!.copyWith(fontWeight: FontWeight.w700)),
                  ],
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('$startTime – $endTime', style: theme.textTheme.titleMedium),
                    Text(
                      entry.comment.isNotEmpty ? entry.comment : Format.date(entry.start),
                      style: theme.textTheme.bodyMedium!.copyWith(color: colors.muted),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(EntryTimes.durationLabel(minutes < 0 ? 0 : minutes), style: theme.textTheme.titleMedium),
                  if (pay > 0)
                    Text(Format.currency(pay), style: theme.textTheme.bodyMedium!.copyWith(color: colors.pay)),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class DismissibleEntryListItem extends StatelessWidget {
  const DismissibleEntryListItem({
    super.key,
    required this.dismissibleKey,
    required this.entry,
    required this.job,
    this.onDismissed,
    this.onTap,
  });

  final Key dismissibleKey;
  final Entry entry;
  final Job job;
  final VoidCallback? onDismissed;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Dismissible(
        background: const DeleteSwipeBackground(),
        key: dismissibleKey,
        direction: DismissDirection.endToStart,
        onDismissed: (direction) => onDismissed?.call(),
        child: EntryListItem(entry: entry, job: job, onTap: onTap),
      ),
    );
  }
}
