import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:starter_architecture_flutter_firebase/src/features/authentication/data/account_deletion_service.dart';
import 'package:starter_architecture_flutter_firebase/src/features/authentication/presentation/delete_account_and_data_button.dart';

class MockAccountDeletionService extends Mock implements AccountDeletionService {}

void main() {
  late MockAccountDeletionService service;
  late int reauthCalls;
  late bool reauthResult;

  setUp(() {
    service = MockAccountDeletionService();
    reauthCalls = 0;
    reauthResult = true;
    when(() => service.deleteAccount()).thenAnswer((_) async {});
  });

  Future<void> pump(WidgetTester tester) => tester.pumpWidget(ProviderScope(
        overrides: [accountDeletionServiceProvider.overrideWithValue(service)],
        child: MaterialApp(
          home: Scaffold(
            body: DeleteAccountAndDataButton(reauthenticate: (_) async {
              reauthCalls++;
              return reauthResult;
            }),
          ),
        ),
      ));

  Future<void> tapDeleteThen(WidgetTester tester, String choice) async {
    await tester.tap(find.byKey(DeleteAccountAndDataButton.buttonKey));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(TextButton, choice));
    await tester.pumpAndSettle();
  }

  testWidgets('the confirm dialog says the jobs and entries are deleted first', (tester) async {
    await pump(tester);
    await tester.tap(find.byKey(DeleteAccountAndDataButton.buttonKey));
    await tester.pumpAndSettle();
    expect(find.textContaining('jobs and time entries'), findsOneWidget);
    expect(find.textContaining('cannot be undone'), findsOneWidget);
  });

  testWidgets('confirming deletes the account and its data', (tester) async {
    await pump(tester);
    await tapDeleteThen(tester, 'Delete');
    verify(() => service.deleteAccount()).called(1);
  });

  testWidgets('cancelling deletes nothing', (tester) async {
    await pump(tester);
    await tapDeleteThen(tester, 'Cancel');
    verifyNever(() => service.deleteAccount());
  });

  testWidgets('asks for a fresh sign-in, then retries, when Firebase requires it', (tester) async {
    var calls = 0;
    when(() => service.deleteAccount()).thenAnswer((_) async {
      if (calls++ == 0) throw FirebaseAuthException(code: 'requires-recent-login');
    });
    await pump(tester);
    await tapDeleteThen(tester, 'Delete');
    expect(reauthCalls, 1);
    verify(() => service.deleteAccount()).called(2);
  });

  testWidgets('stops if the user cancels the fresh sign-in', (tester) async {
    reauthResult = false;
    when(() => service.deleteAccount())
        .thenThrow(FirebaseAuthException(code: 'requires-recent-login'));
    await pump(tester);
    await tapDeleteThen(tester, 'Delete');
    expect(reauthCalls, 1);
    verify(() => service.deleteAccount()).called(1);
  });
}
