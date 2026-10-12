import 'dart:io';

import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:starter_architecture_flutter_firebase/src/features/authentication/data/account_deletion_service.dart';

import '../../../mocks.dart';

class MockUserDataStore extends Mock implements UserDataStore {}

void main() {
  collectionsGuard();

  late MockFirebaseAuth auth;
  late MockUser user;
  late MockUserDataStore data;
  late AccountDeletionService service;

  setUp(() {
    auth = MockFirebaseAuth();
    user = MockUser();
    data = MockUserDataStore();
    service = AccountDeletionService(auth, data);
    when(() => auth.currentUser).thenReturn(user);
    when(() => user.uid).thenReturn('uid-1');
    when(() => data.deleteAllUserData('uid-1')).thenAnswer((_) async {});
    when(() => user.delete()).thenAnswer((_) async {});
  });

  test('deletes the jobs and entries before the account', () async {
    await service.deleteAccount();
    verifyInOrder([
      () => data.deleteAllUserData('uid-1'),
      () => user.delete(),
    ]);
  });

  test('when Firebase needs a recent sign-in, the data is already gone and the error reaches the caller', () async {
    when(() => user.delete())
        .thenThrow(FirebaseAuthException(code: 'requires-recent-login'));
    await expectLater(
      service.deleteAccount(),
      throwsA(isA<FirebaseAuthException>()
          .having((e) => e.code, 'code', 'requires-recent-login')),
    );
    verify(() => data.deleteAllUserData('uid-1')).called(1);
  });

  test('does not delete the account when deleting the data fails', () async {
    when(() => data.deleteAllUserData('uid-1'))
        .thenThrow(FirebaseException(plugin: 'cloud_firestore'));
    await expectLater(service.deleteAccount(), throwsA(isA<FirebaseException>()));
    verifyNever(() => user.delete());
  });

  test('refuses to run without a signed-in user', () async {
    when(() => auth.currentUser).thenReturn(null);
    await expectLater(service.deleteAccount(), throwsStateError);
    verifyNever(() => data.deleteAllUserData(any()));
  });
}

// Firestore clients can't list subcollections, so the deletion list is written by hand. This guard fails the day a
// repository starts writing a new collection under users/{uid} that account deletion would leave behind.
void collectionsGuard() {
  test('account deletion covers every collection the repositories write under users/{uid}', () {
    final pathPattern = RegExp(r"'users/\$uid/(\w+)'");
    final written = <String>{};
    for (final file in Directory('lib').listSync(recursive: true).whereType<File>()) {
      if (!file.path.endsWith('_repository.dart')) continue;
      final code = file
          .readAsStringSync()
          .replaceAll(RegExp(r'/\*[\s\S]*?\*/'), '')
          .replaceAll(RegExp(r'//[^\n]*'), '');
      written.addAll(pathPattern.allMatches(code).map((m) => m.group(1)!));
    }
    final deleted = FirestoreUserDataStore.collectionsOf('uid').map((p) => p.split('/').last).toSet();
    expect(written, isNotEmpty);
    expect(deleted, containsAll(written));
  });
}
