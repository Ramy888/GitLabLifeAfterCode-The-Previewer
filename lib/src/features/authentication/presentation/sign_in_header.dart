import 'package:flutter/material.dart';
import 'package:starter_architecture_flutter_firebase/src/common_widgets/app_logo.dart';
import 'package:starter_architecture_flutter_firebase/src/localization/string_hardcoded.dart';
import 'package:starter_architecture_flutter_firebase/src/theme/app_theme.dart';

/// Brand block shown above the sign-in form on phones and beside it on wide screens.
class SignInHeader extends StatelessWidget {
  const SignInHeader({super.key, this.logoSize = 72, this.showPoints = false});
  final double logoSize;

  /// The wide layout has room for what the app does.
  final bool showPoints;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final muted = AppColors.of(context).muted;
    Widget point(IconData icon, String text) => Padding(
          padding: const EdgeInsets.only(top: 12),
          child: Row(
            children: [
              Icon(icon, color: theme.colorScheme.primary),
              const SizedBox(width: 12),
              Expanded(child: Text(text, style: theme.textTheme.bodyLarge)),
            ],
          ),
        );
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: showPoints ? CrossAxisAlignment.start : CrossAxisAlignment.center,
      children: [
        AppLogo(size: logoSize),
        const SizedBox(height: 16),
        Text('Time Tracker'.hardcoded,
            style: theme.textTheme.headlineMedium!.copyWith(fontWeight: FontWeight.w800)),
        const SizedBox(height: 4),
        Text(
          'Log the hours you work on each job and see your pay, day by day.'.hardcoded,
          textAlign: showPoints ? TextAlign.start : TextAlign.center,
          style: theme.textTheme.bodyLarge!.copyWith(color: muted),
        ),
        if (showPoints) ...[
          const SizedBox(height: 12),
          point(Icons.work_outline_rounded, 'Jobs: one per client, project or shift'.hardcoded),
          point(Icons.timelapse_outlined, 'Entries: a start and a duration, logged in seconds'.hardcoded),
          point(Icons.receipt_long_outlined, 'Timesheet: hours and pay per day'.hardcoded),
        ],
      ],
    );
  }
}
