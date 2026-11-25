# Render deployment checklist

## Important security design
- The site URL is public, but the dashboard and all API endpoints require Django login.
- The repository may be public only after checking that no secrets, credentials, or private data are included.
- `creditcard.csv`, `db.sqlite3`, `.env`, and virtual environments must not be committed.
- This is an educational dataset-replay/demo, not a production payment authorization service.

## GitHub
1. Create a **public** GitHub repository after completing the security checks.
2. Upload the contents of this project folder (not the enclosing ZIP folder).
3. Check that `data/creditcard.csv`, `db.sqlite3`, `.env`, and `venv/` are not in GitHub.
4. Keep `artifacts/fraud_model.joblib` because the app needs the trained model. Only commit artifacts you generated and trust.

## Render
1. Create a PostgreSQL database in Render.
2. Create a Python Web Service connected to the public GitHub repository.
3. Set the service Root Directory to the folder containing `manage.py` (if the repository root is this project folder, leave it blank).
4. Build Command: `./build.sh`
5. Start Command: `gunicorn fraudsite.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120`
6. Add environment variables:
   - `SECRET_KEY`: use Render's Generate option; never paste it into source code.
   - `DATABASE_URL`: use the database's **Internal Database URL** from Render.
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: optional comma-separated additional hostnames; Render hostname is added automatically.
7. Deploy. HTTPS is provided by Render; Django is configured to trust Render's forwarded HTTPS header and redirect HTTP to HTTPS.
8. In the Web Service's Shell, run `python manage.py createsuperuser`.
9. Visit `/accounts/login/` and sign in. The root dashboard redirects unauthenticated visitors to login.

## Data replay note
The original CSV is deliberately excluded from this deployment package because it is large and should not be committed to Git. Without it, the dashboard still loads the saved model metrics and manual scoring can work, but the dataset replay button has no source CSV. Add the dataset later through an appropriately secured private storage/persistent disk workflow if replay is required.

## Before making the service public
- Confirm `/` redirects to `/accounts/login/` when logged out.
- Confirm `/api/stats/` and `/api/transactions/` also require login.
- Confirm `/admin/` requires staff login.
- Confirm `DEBUG=False`, strong generated `SECRET_KEY`, PostgreSQL, and HTTPS.
- Run `python manage.py check --deploy` in the Render shell and address any warnings.
- Use a strong unique admin password and enable MFA on GitHub/Render accounts.
