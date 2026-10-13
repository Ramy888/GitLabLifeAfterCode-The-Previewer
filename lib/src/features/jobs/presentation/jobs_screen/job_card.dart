import 'package:flutter/material.dart';
import 'package:starter_architecture_flutter_firebase/src/features/jobs/domain/job.dart';
import 'package:starter_architecture_flutter_firebase/src/localization/string_hardcoded.dart';
import 'package:starter_architecture_flutter_firebase/src/theme/app_theme.dart';
import 'package:starter_architecture_flutter_firebase/src/utils/alert_dialogs.dart';
import 'package:starter_architecture_flutter_firebase/src/utils/format.dart';

/// One job in the Jobs list: its initial, name and hourly rate.
class JobCard extends StatelessWidget {
  const JobCard({super.key, required this.job, this.onTap});
  final Job job;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = AppColors.of(context);
    final rate = job.ratePerHour > 0 ? '${Format.currency(job.ratePerHour)} / hour' : 'Unpaid'.hardcoded;
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          child: Row(
            children: [
              CircleAvatar(
                backgroundColor: theme.colorScheme.primaryContainer,
                foregroundColor: theme.colorScheme.onPrimaryContainer,
                child: Text(job.name.isEmpty ? '?' : job.name.characters.first.toUpperCase()),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(job.name,
                        style: theme.textTheme.titleMedium, maxLines: 1, overflow: TextOverflow.ellipsis),
                    const SizedBox(height: 2),
                    Text(rate,
                        style: theme.textTheme.bodyMedium!
                            .copyWith(color: job.ratePerHour > 0 ? colors.pay : colors.muted)),
                  ],
                ),
              ),
              Icon(Icons.chevron_right, color: colors.muted),
            ],
          ),
        ),
      ),
    );
  }
}

/// Shown when the user has no jobs yet: what a job is, and a way to add the first one.
class JobsEmptyState extends StatelessWidget {
  const JobsEmptyState({super.key, required this.onAdd});
  final VoidCallback onAdd;

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
              Icon(Icons.work_outline_rounded, size: 64, color: theme.colorScheme.primary),
              const SizedBox(height: 16),
              Text('No jobs yet'.hardcoded, style: theme.textTheme.headlineSmall, textAlign: TextAlign.center),
              const SizedBox(height: 8),
              Text(
                'A job is anything you track time for: a client, a project or a shift. Add one, then log the hours '
                        'you work on it.'
                    .hardcoded,
                style: theme.textTheme.bodyLarge!.copyWith(color: AppColors.of(context).muted),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              FilledButton.icon(onPressed: onAdd, icon: const Icon(Icons.add), label: Text('New job'.hardcoded)),
            ],
          ),
        ),
      ),
    );
  }
}

/// Asks before a job is deleted, because its time entries go with it.
Future<bool> confirmJobDelete(BuildContext context, Job job) async {
  final confirmed = await showAlertDialog(
    context: context,
    title: 'Delete "${job.name}"?'.hardcoded,
    content: 'This also deletes every time entry logged for this job. It cannot be undone.'.hardcoded,
    cancelActionText: 'Cancel'.hardcoded,
    defaultActionText: 'Delete'.hardcoded,
  );
  return confirmed == true;
}
