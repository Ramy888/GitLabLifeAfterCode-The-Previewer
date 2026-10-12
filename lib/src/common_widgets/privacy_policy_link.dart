import 'package:flutter/material.dart';
import 'package:starter_architecture_flutter_firebase/src/constants/app_links.dart';
import 'package:starter_architecture_flutter_firebase/src/localization/string_hardcoded.dart';
import 'package:url_launcher/url_launcher.dart';

/// Opens the published privacy policy (Apple 5.1.1 and Google Play both want it reachable inside the app).
class PrivacyPolicyLink extends StatelessWidget {
  const PrivacyPolicyLink({super.key, this.open = _openExternally});

  /// Overridable for tests.
  final Future<void> Function(Uri uri) open;

  static Future<void> _openExternally(Uri uri) async {
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  @override
  Widget build(BuildContext context) {
    return TextButton.icon(
      onPressed: () => open(AppLinks.privacyPolicy),
      icon: const Icon(Icons.privacy_tip_outlined, size: 18),
      label: Text('Privacy policy'.hardcoded),
    );
  }
}
