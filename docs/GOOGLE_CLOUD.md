# AIAMS on Google Cloud

Cloud Run hosts Django at an automatically secured `https://...run.app` address.
The downloaded Android app connects to this backend. A custom domain is optional.
Use Cloud SQL PostgreSQL for durable data, a private Cloud Storage bucket for
resumes, and Secret Manager for secrets. Hosting and AI usage are separate costs
from Google Play subscriptions.

## First setup

1. Create a Google Cloud project named AIAMS at https://console.cloud.google.com/.
   Note its project ID (not the display name) and link a billing account.
2. Open Cloud Shell and clone this repository. Choose one region, e.g. us-central1.
3. Enable Cloud Run, Cloud Build, Artifact Registry, Cloud SQL Admin, Secret
   Manager, IAM Service Account Credentials, and Google Play Android Developer APIs.
4. Create a runtime service account `aiams-runtime`. Give it Cloud SQL Client.
5. Create a PostgreSQL Cloud SQL instance, database `aiams` and an app database
   user. Enable backups. Use its instance connection name in the database URL:
   `postgresql://USER:URL_ENCODED_PASSWORD@/aiams?host=/cloudsql/PROJECT:REGION:INSTANCE`.
6. Create a regional bucket with uniform bucket-level access and public access
   prevention. Grant the runtime service account Storage Object User on that bucket.
   Grant it Service Account Token Creator on itself if signed file URLs are used.
7. Store a strong, stable Django key as Secret Manager secret `aiams-django-key`
   and the database URL as `aiams-database-url`. Grant runtime Secret Accessor
   on those two secrets. Do not paste their values in chat or commit them.

## Build and deploy

These Cloud Shell commands assume the resources above already exist. Substitute
your nonsecret identifiers. No resources have been created by this implementation.

```bash
PROJECT=your-project-id
REGION=us-central1
INSTANCE=your-sql-instance
BUCKET=your-private-resume-bucket
RUNTIME="aiams-runtime@$PROJECT.iam.gserviceaccount.com"
IMAGE="$REGION-docker.pkg.dev/$PROJECT/aiams/server:initial"
gcloud artifacts repositories create aiams --repository-format=docker --location="$REGION" --project="$PROJECT"
gcloud builds submit --tag="$IMAGE" --project="$PROJECT" .
```

Deploy once privately to obtain the service URL. The temporary settings below
allow boot but do not use real accounts or persistent data until configured.

```bash
gcloud run deploy aiams --image="$IMAGE" --region="$REGION" --project="$PROJECT" --service-account="$RUNTIME" --no-allow-unauthenticated --max-instances=3
APP_URL=$(gcloud run services describe aiams --region="$REGION" --project="$PROJECT" --format='value(status.url)')
APP_HOST=${APP_URL#https://}
```

Configure production and run migrations as a separate Cloud Run Job. The job's
service account needs the same SQL, secret and storage access as the service.

```bash
gcloud run jobs deploy aiams-migrate --image="$IMAGE" --region="$REGION" --project="$PROJECT" --service-account="$RUNTIME" --set-cloudsql-instances="$PROJECT:$REGION:$INSTANCE" --set-secrets=DJANGO_SECRET_KEY=aiams-django-key:latest,DATABASE_URL=aiams-database-url:latest --set-env-vars="DEPLOYMENT_ENV=production,DJANGO_ALLOWED_HOSTS=$APP_HOST,GS_BUCKET_NAME=$BUCKET" --command=python --args=manage.py,migrate,--noinput --max-retries=0 --tasks=1
gcloud run jobs execute aiams-migrate --region="$REGION" --project="$PROJECT" --wait
gcloud run services update aiams --region="$REGION" --project="$PROJECT" --add-cloudsql-instances="$PROJECT:$REGION:$INSTANCE" --set-secrets=DJANGO_SECRET_KEY=aiams-django-key:latest,DATABASE_URL=aiams-database-url:latest --set-env-vars="DEPLOYMENT_ENV=production,DJANGO_ALLOWED_HOSTS=$APP_HOST,GS_BUCKET_NAME=$BUCKET,BILLING_REQUIRED=true,PLAY_PACKAGE_NAME=com.britcrit.aiams"
```

After verifying the configuration, expose the service for app users:

```bash
gcloud run services add-iam-policy-binding aiams --region="$REGION" --project="$PROJECT" --member=allUsers --role=roles/run.invoker
```

Cloud Run public invocation permits the login page to load; Django still enforces
account and subscription access. Keep the bucket private. Complete Play Console
service-account permissions per ANDROID_RELEASE.md before testing purchases.
Build Android with `-PappUrl=` set to the actual APP_URL printed by Cloud Run.
Redeploy migrations as a job before later schema-dependent service revisions.

Reference: https://docs.cloud.google.com/python/django/run
