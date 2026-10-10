# Keyless deploy to Cloud Run from GitLab CI

The `deploy:cloudrun` job never stores a Google key. GitLab issues a short-lived OIDC token for the job (`id_tokens`),
Google's Workload Identity Federation exchanges it for temporary credentials of the `gitlab-deployer` service
account, and `deploy/cloudrun/deploy.sh` runs `gcloud run deploy`.

```
GitLab job ──OIDC token (aud = GCP_WIF_AUDIENCE)──▶ Google STS ──▶ gitlab-deployer@the-previewer-lac ──▶ Cloud Run
```

## Already done (2026-10-10)

`deploy/cloudrun/setup_wif.sh` created, in project `the-previewer-lac`:
- the service account `gitlab-deployer`, with only the roles a source deploy needs (Cloud Run admin, Cloud Build editor,
  Artifact Registry writer, Storage admin for the source bucket, service account user, Service Usage consumer)
- the workload identity pool `gitlab` and the OIDC provider `gitlab-com` (issuer `https://gitlab.com`)
- an **interim** trust rule: only pipelines started by GitLab user `RamyoZo`, on protected branches or tags

## When the GitLab project exists

1. Lock the trust to that one project. Re-run with its full path, for example:
   ```sh
   GITLAB_PROJECT_PATH=gitlab-com/hackathon/transcend/ramyozo/the-previewer sh deploy/cloudrun/setup_wif.sh
   ```
   Then remove the interim binding (it is safe to keep, but narrower is better):
   ```sh
   gcloud iam service-accounts remove-iam-policy-binding gitlab-deployer@the-previewer-lac.iam.gserviceaccount.com \
     --project the-previewer-lac --role roles/iam.workloadIdentityUser \
     --member "principalSet://iam.googleapis.com/projects/57342278583/locations/global/workloadIdentityPools/gitlab/attribute.user_login/RamyoZo"
   ```
2. In GitLab, go to **Settings > CI/CD > Variables** and add the values from `.env`:
   - Plain (not secret): `GCP_PROJECT_ID`, `GCP_REGION`, `GCP_WIF_PROVIDER`, `GCP_WIF_AUDIENCE`, `GCP_SERVICE_ACCOUNT`, `CLOUD_RUN_URL`
   - Masked: `FIREBASE_OPTIONS_DART`, `GOOGLE_SERVICES_JSON`, `STORE_REVIEW_DEMO_LOGIN` (masked, **not** protected)
3. Make sure the default branch is protected (the trust rule requires `ref_protected`).
4. Run a pipeline on the default branch and start `deploy:cloudrun` (it is manual). The job prints the service URL.

## If it fails

| Error | Cause |
|---|---|
| `The audience in ID Token ... does not match` | `GCP_WIF_AUDIENCE` differs from the provider's allowed audience |
| `The given credential is rejected by the attribute condition` | Wrong project path, an unprotected branch, or a pipeline started by another user (interim rule) |
| `Permission 'iam.serviceAccounts.getAccessToken' denied` | The `workloadIdentityUser` binding is missing for this project path |
| `Refusing to deploy: ... stub Firebase config` | `FIREBASE_OPTIONS_DART` is not set for the build |
