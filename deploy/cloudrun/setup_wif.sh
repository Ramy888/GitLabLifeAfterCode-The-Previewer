#!/usr/bin/env sh
# One-time Google Cloud setup so GitLab CI can deploy to Cloud Run without any stored key
# (Workload Identity Federation). Safe to re-run.
#
#   GITLAB_PROJECT_PATH=group/subgroup/project sh deploy/cloudrun/setup_wif.sh   # final, locked to one project
#   GITLAB_USER_LOGIN=RamyoZo sh deploy/cloudrun/setup_wif.sh                     # interim, before the project exists
#
# Prints the CI/CD variables to set in GitLab at the end.
set -eu
PROJECT="${GCP_PROJECT_ID:-the-previewer-lac}"
NUM="$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')"
POOL=gitlab
PROVIDER=gitlab-com
SA_NAME=gitlab-deployer
SA="$SA_NAME@$PROJECT.iam.gserviceaccount.com"
AUDIENCE="https://iam.googleapis.com/projects/$NUM/locations/global/workloadIdentityPools/$POOL/providers/$PROVIDER"

if [ -n "${GITLAB_PROJECT_PATH:-}" ]; then
  CONDITION="assertion.project_path == '$GITLAB_PROJECT_PATH' && assertion.ref_protected == 'true'"
  MEMBER="principalSet://iam.googleapis.com/projects/$NUM/locations/global/workloadIdentityPools/$POOL/attribute.project_path/$GITLAB_PROJECT_PATH"
elif [ -n "${GITLAB_USER_LOGIN:-}" ]; then
  CONDITION="assertion.user_login == '$GITLAB_USER_LOGIN' && assertion.ref_protected == 'true'"
  MEMBER="principalSet://iam.googleapis.com/projects/$NUM/locations/global/workloadIdentityPools/$POOL/attribute.user_login/$GITLAB_USER_LOGIN"
else
  echo "Set GITLAB_PROJECT_PATH (preferred) or GITLAB_USER_LOGIN" >&2
  exit 2
fi

gcloud services enable iamcredentials.googleapis.com sts.googleapis.com run.googleapis.com \
  cloudbuild.googleapis.com artifactregistry.googleapis.com --project "$PROJECT" --quiet

gcloud iam service-accounts describe "$SA" --project "$PROJECT" >/dev/null 2>&1 ||
  gcloud iam service-accounts create "$SA_NAME" --project "$PROJECT" --display-name "GitLab CI deployer (Cloud Run)"
for role in roles/run.admin roles/cloudbuild.builds.editor roles/artifactregistry.writer roles/storage.admin \
            roles/serviceusage.serviceUsageConsumer roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding "$PROJECT" --member "serviceAccount:$SA" --role "$role" \
    --condition=None --quiet >/dev/null
done

gcloud iam workload-identity-pools describe "$POOL" --project "$PROJECT" --location global >/dev/null 2>&1 ||
  gcloud iam workload-identity-pools create "$POOL" --project "$PROJECT" --location global --display-name "GitLab"

MAPPING="google.subject=assertion.sub,attribute.project_path=assertion.project_path,attribute.user_login=assertion.user_login,attribute.ref=assertion.ref,attribute.ref_protected=assertion.ref_protected"
if gcloud iam workload-identity-pools providers describe "$PROVIDER" --project "$PROJECT" --location global \
     --workload-identity-pool "$POOL" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools providers update-oidc "$PROVIDER" --project "$PROJECT" --location global \
    --workload-identity-pool "$POOL" --attribute-mapping "$MAPPING" --attribute-condition "$CONDITION" \
    --allowed-audiences "$AUDIENCE" --quiet
else
  gcloud iam workload-identity-pools providers create-oidc "$PROVIDER" --project "$PROJECT" --location global \
    --workload-identity-pool "$POOL" --issuer-uri "https://gitlab.com" --attribute-mapping "$MAPPING" \
    --attribute-condition "$CONDITION" --allowed-audiences "$AUDIENCE"
fi

gcloud iam service-accounts add-iam-policy-binding "$SA" --project "$PROJECT" \
  --role roles/iam.workloadIdentityUser --member "$MEMBER" --quiet >/dev/null

cat <<VARS

Set these CI/CD variables in GitLab (Settings > CI/CD > Variables). None of them is a secret:
  GCP_PROJECT_ID      = $PROJECT
  GCP_REGION          = ${GCP_REGION:-us-central1}
  GCP_WIF_PROVIDER    = projects/$NUM/locations/global/workloadIdentityPools/$POOL/providers/$PROVIDER
  GCP_WIF_AUDIENCE    = $AUDIENCE
  GCP_SERVICE_ACCOUNT = $SA
VARS
