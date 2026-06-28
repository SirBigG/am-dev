# AgroMega Forum Instance

This directory is a separate Django/Spirit forum project. It uses the main AgroMega site as its OpenID Connect provider and keeps forum data in its own database.

## Main site setup

Install the main app dependencies and set an RSA private key for OIDC ID token signing:

```bash
python manage.py migrate oauth2_provider
python manage.py ensure_forum_oidc_application \
  --client-id agromega-forum \
  --client-secret "$FORUM_OIDC_CLIENT_SECRET" \
  --redirect-uri "https://forum.example.com/complete/oidc/"
```

Required main-site environment:

```bash
SITE_URL=https://example.com
FORUM_BASE_URL=https://forum.example.com
FORUM_SSO_URL=https://forum.example.com/sso/start/
FORUM_LOGOUT_URL=https://forum.example.com/logout/
OIDC_RSA_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----..."
FORUM_OIDC_CLIENT_SECRET=...
```

## Forum setup

Install forum dependencies separately, then initialize Spirit:

```bash
cd forum_instance
pip install -r requirements.txt
python manage.py migrate
python manage.py spiritinstall
python manage.py collectstatic
```

Required forum environment:

```bash
FORUM_SECRET_KEY=...
FORUM_SITE_URL=https://forum.example.com
MAIN_SITE_URL=https://example.com
FORUM_ALLOWED_HOSTS=forum.example.com
FORUM_CSRF_TRUSTED_ORIGINS=https://forum.example.com
FORUM_POSTGRES_DB=...
FORUM_POSTGRES_USER=...
FORUM_POSTGRES_PASSWORD=...
FORUM_POSTGRES_HOST=...
FORUM_POSTGRES_PORT=5432
FORUM_OIDC_ENDPOINT=https://example.com/o
FORUM_OIDC_CLIENT_ID=agromega-forum
FORUM_OIDC_CLIENT_SECRET=...
```

The forum menu in the main site points to `/sso/start/` on the forum host. Direct visits to the forum remain readable anonymously; write actions use the forum login URL and redirect through OIDC to the main site.
