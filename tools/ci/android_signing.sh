#!/usr/bin/env sh
# Write android/key.properties and the upload keystore from masked CI/CD variables.
set -eu
: "${ANDROID_KEYSTORE_BASE64:?}" "${ANDROID_KEYSTORE_PASSWORD:?}" "${ANDROID_KEY_ALIAS:?}" "${ANDROID_KEY_PASSWORD:?}"
printf '%s' "$ANDROID_KEYSTORE_BASE64" | base64 -d > android/upload-keystore.jks
cat > android/key.properties <<PROPS
storeFile=../upload-keystore.jks
storePassword=$ANDROID_KEYSTORE_PASSWORD
keyAlias=$ANDROID_KEY_ALIAS
keyPassword=$ANDROID_KEY_PASSWORD
PROPS
echo "android signing: key.properties written"
