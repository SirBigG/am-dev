#!/bin/sh
set -eu

touch /var/log/nginx/.logrotate-last-success
cron
exec /docker-entrypoint.sh "$@"
