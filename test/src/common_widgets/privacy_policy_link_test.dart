import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:starter_architecture_flutter_firebase/src/common_widgets/privacy_policy_link.dart';
import 'package:starter_architecture_flutter_firebase/src/constants/app_links.dart';

void main() {
  testWidgets('shows a tappable Privacy policy link that opens the published policy', (tester) async {
    Uri? opened;
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(body: PrivacyPolicyLink(open: (uri) async => opened = uri)),
    ));
    await tester.tap(find.text('Privacy policy'));
    await tester.pump();
    expect(opened, AppLinks.privacyPolicy);
  });

  test('the in-app privacy link matches the listing the stores see', () {
    final listing = RegExp(r'^privacy_policy_url:\s*(\S+)', multiLine: true)
        .firstMatch(File('store/listing.yaml').readAsStringSync())!
        .group(1);
    expect(AppLinks.privacyPolicy.toString(), listing);
  });
}
