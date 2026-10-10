#!/usr/bin/env sh
# Deploy build/web to Cloud Run from GitLab CI using Workload Identity Federation (no long-lived keys).
# Required CI/CD variables: GCP_PROJECT_ID, GCP_REGION, GCP_WIF_PROVIDER (full provider resource name),
# GCP_SERVICE_ACCOUNT. GCP_ID_TOKEN comes from the job's id_tokens block.
set -eu
: "${GCP_PROJECT_ID:?}" "${GCP_REGION:?}" "${GCP_WIF_PROVIDER:?}" "${GCP_SERVICE_ACCOUNT:?}" "${GCP_ID_TOKEN:?}"
SERVICE="${CLOUD_RUN_SERVICE:-time-tracker-web}"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp" deploy/cloudrun/web' EXIT

printf '%s' "$GCP_ID_TOKEN" > "$tmp/token"
gcloud iam workload-identity-pools create-cred-config "$GCP_WIF_PROVIDER" \
  --service-account="$GCP_SERVICE_ACCOUNT" --credential-source-file="$tmp/token" --output-file="$tmp/cred.json"
gcloud auth login --cred-file="$tmp/cred.json" --quiet

rm -rf deploy/cloudrun/web
cp -R build/web deploy/cloudrun/web
gcloud run deploy "$SERVICE" --source deploy/cloudrun --project "$GCP_PROJECT_ID" --region "$GCP_REGION" \
  --allow-unauthenticated --port 8080 --quiet
gcloud run services describe "$SERVICE" --project "$GCP_PROJECT_ID" --region "$GCP_REGION" --format 'value(status.url)'
