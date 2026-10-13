import 'package:firebase_ui_auth/firebase_ui_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:starter_architecture_flutter_firebase/src/features/authentication/data/firebase_auth_repository.dart';
import 'package:starter_architecture_flutter_firebase/src/features/authentication/presentation/account_body.dart';
import 'package:starter_architecture_flutter_firebase/src/features/authentication/presentation/delete_account_and_data_button.dart';
import 'package:starter_architecture_flutter_firebase/src/localization/string_hardcoded.dart';

/// The Account tab. Built from FirebaseUI's profile widgets instead of its ProfileScreen, whose delete button
/// removes only the sign-in account and can't be replaced; [DeleteAccountAndDataButton] deletes the user's data first.
class CustomProfileScreen extends ConsumerWidget {
  const CustomProfileScreen({super.key});

  /// Set at build time with `--dart-define=APP_VERSION=<pubspec version>`.
  static const appVersion = String.fromEnvironment('APP_VERSION');

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(firebaseAuthProvider);
    final user = auth.currentUser;
    return Scaffold(
      appBar: AppBar(title: Text('Account'.hardcoded)),
      body: AccountBody(
        avatar: UserAvatar(auth: auth, size: 96),
        name: EditableUserDisplayName(auth: auth),
        email: user?.email,
        isAnonymous: user?.isAnonymous ?? false,
        onSignOut: () => auth.signOut(),
        deleteButton: const DeleteAccountAndDataButton(),
        version: appVersion,
      ),
    );
  }
}
