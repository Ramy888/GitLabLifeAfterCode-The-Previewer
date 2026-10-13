import 'package:flutter/material.dart';
import 'package:starter_architecture_flutter_firebase/src/common_widgets/privacy_policy_link.dart';
import 'package:starter_architecture_flutter_firebase/src/common_widgets/responsive_center.dart';
import 'package:starter_architecture_flutter_firebase/src/localization/string_hardcoded.dart';
import 'package:starter_architecture_flutter_firebase/src/theme/app_theme.dart';
import 'package:starter_architecture_flutter_firebase/src/utils/alert_dialogs.dart';

/// The Account tab's content, free of Firebase so it can be laid out and tested on its own.
/// [CustomProfileScreen] passes in the FirebaseUI avatar and name editor, the user's details and the sign-out action.
class AccountBody extends StatelessWidget {
  const AccountBody({
    super.key,
    required this.avatar,
    required this.name,
    required this.email,
    required this.isAnonymous,
    required this.onSignOut,
    required this.deleteButton,
    this.version = '',
  });

  final Widget avatar;
  final Widget name;
  final String? email;
  final bool isAnonymous;
  final VoidCallback onSignOut;
  final Widget deleteButton;
  final String version;

  static const signOutKey = Key('sign-out');

  Future<void> _signOut(BuildContext context) async {
    if (isAnonymous) {
      // An anonymous account can't be signed back into: its jobs and entries would be stranded.
      final confirmed = await showAlertDialog(
        context: context,
        title: 'Sign out of this anonymous account?'.hardcoded,
        content: 'You have no email or password, so after signing out your jobs and time entries cannot be '
                'recovered. To keep them, stay signed in.'
            .hardcoded,
        cancelActionText: 'Cancel'.hardcoded,
        defaultActionText: 'Sign out anyway'.hardcoded,
      );
      if (confirmed != true) return;
    }
    onSignOut();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = AppColors.of(context);
    return ResponsiveCenter(
      maxContentWidth: 560,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  avatar,
                  const SizedBox(height: 16),
                  name,
                  const SizedBox(height: 8),
                  if (isAnonymous)
                    Chip(
                      avatar: const Icon(Icons.visibility_off_outlined, size: 18),
                      label: Text('Anonymous'.hardcoded),
                    )
                  else if (email != null)
                    Text(email!, style: theme.textTheme.bodyMedium!.copyWith(color: colors.muted)),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          FilledButton.tonalIcon(
            key: signOutKey,
            onPressed: () => _signOut(context),
            icon: const Icon(Icons.logout),
            label: Text('Sign out'.hardcoded),
          ),
          const SizedBox(height: 24),
          Card(
            color: theme.colorScheme.errorContainer.withValues(alpha: 0.35),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text('Danger zone'.hardcoded,
                      style: theme.textTheme.titleMedium!.copyWith(color: theme.colorScheme.error)),
                  const SizedBox(height: 4),
                  Text(
                    'Deletes all your jobs and time entries, then your account.'.hardcoded,
                    style: theme.textTheme.bodySmall!.copyWith(color: colors.muted),
                  ),
                  const SizedBox(height: 12),
                  deleteButton,
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          const Center(child: PrivacyPolicyLink()),
          if (version.isNotEmpty)
            Center(
              child: Text('Time Tracker $version',
                  style: theme.textTheme.bodySmall!.copyWith(color: colors.muted)),
            ),
        ],
      ),
    );
  }
}
