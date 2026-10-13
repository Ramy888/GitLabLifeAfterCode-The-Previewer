import 'package:firebase_ui_auth/firebase_ui_auth.dart';
import 'package:flutter/material.dart';
import 'package:starter_architecture_flutter_firebase/src/common_widgets/privacy_policy_link.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:starter_architecture_flutter_firebase/src/constants/app_sizes.dart';
import 'package:starter_architecture_flutter_firebase/src/features/authentication/data/firebase_auth_repository.dart';
import 'package:starter_architecture_flutter_firebase/src/utils/alert_dialogs.dart';

import 'auth_providers.dart';
import 'sign_in_header.dart';

class CustomSignInScreen extends ConsumerWidget {
  const CustomSignInScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authProviders = ref.watch(authProvidersProvider);
    return SignInScreen(
      providers: authProviders,
      headerMaxExtent: 220,
      headerBuilder: (context, constraints, shrinkOffset) => const Padding(
        padding: EdgeInsets.only(top: 24),
        child: Center(child: SignInHeader(logoSize: 64)),
      ),
      sideBuilder: (context, constraints) => const Center(
        child: Padding(
          padding: EdgeInsets.all(48),
          child: SignInHeader(logoSize: 96, showPoints: true),
        ),
      ),
      footerBuilder: (context, action) => const SignInAnonymouslyFooter(),
    );
  }
}

class SignInAnonymouslyFooter extends ConsumerWidget {
  const SignInAnonymouslyFooter({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Column(
      children: [
        gapH8,
        const Row(
          children: [
            Expanded(child: Divider()),
            Padding(
              padding: EdgeInsets.symmetric(horizontal: Sizes.p8),
              child: Text('or'),
            ),
            Expanded(child: Divider()),
          ],
        ),
        TextButton(
          onPressed: () async {
            try {
              await ref.read(firebaseAuthProvider).signInAnonymously();
            } catch (e) {
              if (context.mounted) {
                await showExceptionAlertDialog(
                  context: context,
                  title: 'Error',
                  exception: e,
                );
              }
            }
          },
          child: const Text('Sign in anonymously'),
        ),
        const PrivacyPolicyLink(),
      ],
    );
  }
}
