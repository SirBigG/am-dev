#!/bin/sh
set -e

# Attempt to create forum DB if it doesn't exist
python /app/ensure_forum_db.py || true

# Run migrations
python manage.py migrate --noinput
python manage.py createcachetable spirit_cache spirit_rl_cache

# Collect static into shared volume (ignore failures)
python manage.py compilemessages --locale uk || true
python manage.py collectstatic --noinput || true
python manage.py update_index --verbosity 0 || true

# Start development server
exec python manage.py runserver 0.0.0.0:8082
