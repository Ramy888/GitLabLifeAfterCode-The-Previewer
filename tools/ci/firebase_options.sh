#!/usr/bin/env sh
# Write lib/firebase_options.dart for CI. The real file is gitignored.
# With FIREBASE_OPTIONS_DART (base64, masked CI/CD variable) set, decode it; otherwise write a stub that compiles
# for tests and analysis but cannot talk to Firebase.
set -eu
out=lib/firebase_options.dart
if [ -n "${FIREBASE_OPTIONS_DART:-}" ]; then
  printf '%s' "$FIREBASE_OPTIONS_DART" | base64 -d > "$out"
  echo "firebase_options.dart: decoded from CI/CD variable"
  exit 0
fi
cat > "$out" <<'DART'
// Stub written by tools/ci/firebase_options.sh. Builds and tests only; it cannot reach Firebase.
import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;

class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform => const FirebaseOptions(
        apiKey: 'stub',
        appId: '1:0:web:0',
        messagingSenderId: '0',
        projectId: 'stub',
      );
}
DART
echo "firebase_options.dart: stub (set FIREBASE_OPTIONS_DART for a real build)"
