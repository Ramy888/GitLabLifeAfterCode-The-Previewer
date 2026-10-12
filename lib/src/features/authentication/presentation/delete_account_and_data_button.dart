import 'package:firebase_auth/firebase_auth.dart' hide EmailAuthProvider;
import 'package:firebase_ui_auth/firebase_ui_auth.dart'
    show showReauthenticateDialog;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:starter_architecture_flutter_firebase/src/features/authentication/data/account_deletion_service.dart';
import 'package:starter_architecture_flutter_firebase/src/features/authentication/presentation/auth_providers.dart';
import 'package:starter_architecture_flutter_firebase/src/localization/string_hardcoded.dart';
import 'package:starter_architecture_flutter_firebase/src/utils/alert_dialogs.dart';

/// Asks the user to sign in again; returns whether they did.
typedef Reauthenticate = Future<bool> Function(BuildContext context);

/// Deletes the user's jobs and time entries, then the account. Replaces FirebaseUI's DeleteAccountButton, which deletes
/// only the account and leaves the Firestore data behind.
class DeleteAccountAndDataButton extends ConsumerStatefulWidget {
  const DeleteAccountAndDataButton({super.key, this.reauthenticate});

  /// Overridable for tests; defaults to FirebaseUI's re-authentication dialog.
  final Reauthenticate? reauthenticate;

  static const buttonKey = Key('delete-account');

  @override
  ConsumerState<DeleteAccountAndDataButton> createState() =>
      _DeleteAccountAndDataButtonState();
}

class _DeleteAccountAndDataButtonState
    extends ConsumerState<DeleteAccountAndDataButton> {
  bool _isLoading = false;

  Future<bool> _defaultReauthenticate(BuildContext context) =>
      showReauthenticateDialog(
        context: context,
        providers: ref.read(authProvidersProvider),
      );

  Future<void> _delete() async {
    final confirmed = await showAlertDialog(
      context: context,
      title: 'Delete account?'.hardcoded,
      content:
          'This permanently deletes all your jobs and time entries, then your account. '
                  'It cannot be undone.'
              .hardcoded,
      cancelActionText: 'Cancel'.hardcoded,
      defaultActionText: 'Delete'.hardcoded,
    );
    if (confirmed != true || !mounted) return;
    setState(() => _isLoading = true);
    try {
      await _deleteWithReauthentication();
    } catch (e) {
      if (mounted) {
        await showExceptionAlertDialog(
          context: context,
          title: 'Could not delete the account'.hardcoded,
          exception: e,
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _deleteWithReauthentication() async {
    final service = ref.read(accountDeletionServiceProvider);
    try {
      await service.deleteAccount();
    } on FirebaseAuthException catch (e) {
      if (e.code != 'requires-recent-login' || !mounted) rethrow;
      // The data is already deleted; only the account needs a fresh sign-in.
      final reauthenticate = widget.reauthenticate ?? _defaultReauthenticate;
      if (await reauthenticate(context)) {
        await service.deleteAccount();
      } else if (mounted) {
        await showAlertDialog(
          context: context,
          title: 'Account not deleted yet'.hardcoded,
          content:
              'Your jobs and time entries were deleted. To delete the account itself, sign in again '
                      'and tap Delete account.'
                  .hardcoded,
          defaultActionText: 'OK'.hardcoded,
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final error = Theme.of(context).colorScheme.error;
    return OutlinedButton.icon(
      key: DeleteAccountAndDataButton.buttonKey,
      // The app theme fills buttons; a destructive action stays outlined in the error colour.
      style: OutlinedButton.styleFrom(
        foregroundColor: error,
        backgroundColor: Colors.transparent,
        side: BorderSide(color: error),
      ),
      onPressed: _isLoading ? null : _delete,
      icon: _isLoading
          ? const SizedBox.square(
              dimension: 16, child: CircularProgressIndicator(strokeWidth: 2))
          : const Icon(Icons.delete_outline),
      label: Text('Delete account'.hardcoded),
    );
  }
}
