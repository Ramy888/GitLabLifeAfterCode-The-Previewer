import 'package:firebase_ui_auth/firebase_ui_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:starter_architecture_flutter_firebase/src/common_widgets/responsive_center.dart';
import 'package:starter_architecture_flutter_firebase/src/features/authentication/data/firebase_auth_repository.dart';
import 'package:starter_architecture_flutter_firebase/src/features/authentication/presentation/delete_account_and_data_button.dart';
import 'package:starter_architecture_flutter_firebase/src/localization/string_hardcoded.dart';

/// The Account tab. Built from FirebaseUI's profile widgets instead of its ProfileScreen, whose delete button
/// removes only the sign-in account and can't be replaced; [DeleteAccountAndDataButton] deletes the user's data first.
class CustomProfileScreen extends ConsumerWidget {
  const CustomProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(firebaseAuthProvider);
    final user = auth.currentUser;
    return Scaffold(
      appBar: AppBar(title: Text('Profile'.hardcoded)),
      body: ResponsiveCenter(
        maxContentWidth: 500,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Center(child: UserAvatar(auth: auth)),
            const SizedBox(height: 16),
            Center(child: EditableUserDisplayName(auth: auth)),
            const SizedBox(height: 8),
            Center(
              child: Text(
                user?.email ?? 'Signed in anonymously'.hardcoded,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ),
            const SizedBox(height: 32),
            SignOutButton(auth: auth, variant: ButtonVariant.outlined),
            const SizedBox(height: 8),
            const DeleteAccountAndDataButton(),
          ],
        ),
      ),
    );
  }
}
