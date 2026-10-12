import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:riverpod/riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:starter_architecture_flutter_firebase/src/features/authentication/data/firebase_auth_repository.dart';
import 'package:starter_architecture_flutter_firebase/src/features/entries/data/entries_repository.dart';
import 'package:starter_architecture_flutter_firebase/src/features/jobs/data/jobs_repository.dart';

part 'account_deletion_service.g.dart';

/// Everything the app stores for one user.
abstract class UserDataStore {
  Future<void> deleteAllUserData(String uid);
}

class FirestoreUserDataStore implements UserDataStore {
  const FirestoreUserDataStore(this._firestore);
  final FirebaseFirestore _firestore;

  // Firestore allows at most 500 writes per batch.
  static const _batchSize = 400;

  /// Every collection the app writes under `users/{uid}`.
  static List<String> collectionsOf(String uid) =>
      [EntriesRepository.entriesPath(uid), JobsRepository.jobsPath(uid)];

  @override
  Future<void> deleteAllUserData(String uid) async {
    for (final path in collectionsOf(uid)) {
      while (true) {
        final page = await _firestore.collection(path).limit(_batchSize).get();
        if (page.docs.isEmpty) break;
        final batch = _firestore.batch();
        for (final doc in page.docs) {
          batch.delete(doc.reference);
        }
        await batch.commit();
      }
    }
  }
}

class AccountDeletionService {
  const AccountDeletionService(this._auth, this._data);
  final FirebaseAuth _auth;
  final UserDataStore _data;

  /// Deletes the user's jobs and entries, then the sign-in account.
  ///
  /// The data goes first because Firestore rules only let a signed-in user delete it. If Firebase needs a recent
  /// sign-in, this throws `requires-recent-login` after the data is gone: re-authenticate and call it again.
  Future<void> deleteAccount() async {
    final user = _auth.currentUser;
    if (user == null) {
      throw StateError('No signed-in user to delete');
    }
    await _data.deleteAllUserData(user.uid);
    await user.delete();
  }
}

@riverpod
AccountDeletionService accountDeletionService(Ref ref) {
  return AccountDeletionService(
    ref.watch(firebaseAuthProvider),
    FirestoreUserDataStore(FirebaseFirestore.instance),
  );
}
