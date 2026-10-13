import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:starter_architecture_flutter_firebase/src/common_widgets/responsive_center.dart';
import 'package:starter_architecture_flutter_firebase/src/constants/strings.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/application/entries_service.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/domain/daily_jobs_details.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/domain/timesheet.dart';
import 'package:starter_architecture_flutter_firebase/src/localization/string_hardcoded.dart';
import 'package:starter_architecture_flutter_firebase/src/theme/app_theme.dart';
import 'package:starter_architecture_flutter_firebase/src/utils/format.dart';

/// The Entries tab: the timesheet across all jobs.
class EntriesScreen extends ConsumerWidget {
  const EntriesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final timesheet = ref.watch(timesheetStreamProvider);
    return Scaffold(
      appBar: AppBar(title: const Text(Strings.entries)),
      body: timesheet.when(
        data: (sheet) => TimesheetView(sheet: sheet),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text(e.toString())),
      ),
    );
  }
}

/// The timesheet, free of Firebase: an explainer, the totals, then one card per day.
class TimesheetView extends StatelessWidget {
  const TimesheetView({super.key, required this.sheet});
  final Timesheet sheet;

  @override
  Widget build(BuildContext context) {
    if (sheet.days.isEmpty) return const EntriesEmptyState();
    return ResponsiveCenter(
      maxContentWidth: 720,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
        children: [
          Text(
            'Your timesheet: hours and pay per day, across all jobs.'.hardcoded,
            style: Theme.of(context).textTheme.bodyMedium!.copyWith(color: AppColors.of(context).muted),
          ),
          const SizedBox(height: 12),
          TotalsStrip(hours: sheet.totalHours, pay: sheet.totalPay),
          const SizedBox(height: 16),
          for (final day in sheet.days) ...[
            DayCard(day: day),
            const SizedBox(height: 12),
          ],
        ],
      ),
    );
  }
}

/// Hours and pay across every entry.
class TotalsStrip extends StatelessWidget {
  const TotalsStrip({super.key, required this.hours, required this.pay});
  final double hours;
  final double pay;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = AppColors.of(context);
    Widget fact(String label, String value, [Color? color]) => Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: theme.textTheme.labelMedium!.copyWith(color: colors.muted)),
              Text(value,
                  style: theme.textTheme.headlineSmall!.copyWith(fontWeight: FontWeight.w700, color: color)),
            ],
          ),
        );
    return Card(
      color: colors.headerFill,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            fact('Total hours'.hardcoded, Format.hours(hours)),
            if (pay > 0) fact('Total pay'.hardcoded, Format.currency(pay), colors.pay),
          ],
        ),
      ),
    );
  }
}

/// One day: its date and totals, then a row per job worked that day.
class DayCard extends StatelessWidget {
  const DayCard({super.key, required this.day});
  final DailyJobsDetails day;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = AppColors.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    '${Format.dayOfWeek(day.date)}, ${Format.date(day.date)}',
                    style: theme.textTheme.titleMedium,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                Text(Format.hours(day.duration), style: theme.textTheme.titleMedium),
                if (day.pay > 0) ...[
                  const SizedBox(width: 12),
                  Text(Format.currency(day.pay),
                      style: theme.textTheme.titleMedium!.copyWith(color: colors.pay)),
                ],
              ],
            ),
            const Divider(height: 20),
            for (final job in day.jobsDetails)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    Icon(Icons.work_outline_rounded, size: 18, color: colors.muted),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(job.name, overflow: TextOverflow.ellipsis, style: theme.textTheme.bodyLarge),
                    ),
                    Text(Format.hours(job.durationInHours), style: theme.textTheme.bodyLarge),
                    if (job.pay > 0) ...[
                      const SizedBox(width: 12),
                      SizedBox(
                        width: 72,
                        child: Text(Format.currency(job.pay),
                            textAlign: TextAlign.right,
                            style: theme.textTheme.bodyLarge!.copyWith(color: colors.pay)),
                      ),
                    ],
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}

/// No entries yet: what this tab is for and how to fill it.
class EntriesEmptyState extends StatelessWidget {
  const EntriesEmptyState({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(32),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.receipt_long_outlined, size: 64, color: theme.colorScheme.primary),
              const SizedBox(height: 16),
              Text('Your timesheet is empty'.hardcoded,
                  style: theme.textTheme.headlineSmall, textAlign: TextAlign.center),
              const SizedBox(height: 8),
              Text(
                'This tab adds up the hours and pay you log, day by day, across all your jobs. To log time, open a '
                        'job in the Jobs tab and tap New entry.'
                    .hardcoded,
                style: theme.textTheme.bodyLarge!.copyWith(color: AppColors.of(context).muted),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
