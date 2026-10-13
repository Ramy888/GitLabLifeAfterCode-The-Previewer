import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:starter_architecture_flutter_firebase/src/features/authentication/presentation/account_body.dart';
import 'package:starter_architecture_flutter_firebase/src/theme/app_theme.dart';

Widget host({required bool anonymous, required VoidCallback onSignOut}) => MaterialApp(
      theme: AppTheme.light(),
      home: Scaffold(
        body: AccountBody(
          avatar: const CircleAvatar(),
          name: const Text('Ramy'),
          email: anonymous ? null : 'ramy@example.com',
          isAnonymous: anonymous,
          version: '2.2.0',
          onSignOut: onSignOut,
          deleteButton: const Text('delete-slot'),
        ),
      ),
    );

void main() {
  testWidgets('a signed-in user signs out without a warning', (tester) async {
    var signedOut = 0;
    await tester.pumpWidget(host(anonymous: false, onSignOut: () => signedOut++));
    expect(find.text('ramy@example.com'), findsOneWidget);
    await tester.tap(find.byKey(AccountBody.signOutKey));
    await tester.pumpAndSettle();
    expect(signedOut, 1);
  });

  testWidgets('an anonymous user is warned first, and cancelling keeps them signed in', (tester) async {
    var signedOut = 0;
    await tester.pumpWidget(host(anonymous: true, onSignOut: () => signedOut++));
    expect(find.text('Anonymous'), findsOneWidget);
    await tester.tap(find.byKey(AccountBody.signOutKey));
    await tester.pumpAndSettle();
    expect(find.textContaining('cannot be recovered'), findsOneWidget);
    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();
    expect(signedOut, 0);
    await tester.tap(find.byKey(AccountBody.signOutKey));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Sign out anyway'));
    await tester.pumpAndSettle();
    expect(signedOut, 1);
  });

  testWidgets('the delete button sits in a danger zone, and the version shows', (tester) async {
    await tester.pumpWidget(host(anonymous: false, onSignOut: () {}));
    expect(find.text('Danger zone'), findsOneWidget);
    expect(find.text('delete-slot'), findsOneWidget);
    expect(find.textContaining('2.2.0'), findsOneWidget);
  });
}
