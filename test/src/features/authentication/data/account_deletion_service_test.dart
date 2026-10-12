import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:starter_architecture_flutter_firebase/src/features/authentication/data/account_deletion_service.dart';

import '../../../mocks.dart';

class MockUserDataStore extends Mock implements UserDataStore {}

void main() {
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
