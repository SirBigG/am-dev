FROM nginx

ARG NGINX_CONF

RUN apt-get update \
    && apt-get install --no-install-recommends -y cron logrotate \
    && rm -rf /var/lib/apt/lists/*

COPY $NGINX_CONF /etc/nginx/nginx.conf
COPY logrotate-nginx.conf /etc/agromega-nginx-logrotate.conf
COPY nginx-logrotate.cron /etc/cron.d/nginx-logrotate
COPY rotate-nginx-logs /usr/local/sbin/rotate-nginx-logs
COPY check-nginx-logs /usr/local/sbin/check-nginx-logs
COPY agromega-entrypoint.sh /usr/local/bin/agromega-entrypoint.sh

RUN chmod 0644 /etc/agromega-nginx-logrotate.conf /etc/cron.d/nginx-logrotate \
    && chmod 0755 /usr/local/sbin/rotate-nginx-logs /usr/local/sbin/check-nginx-logs \
        /usr/local/bin/agromega-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/agromega-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]

HEALTHCHECK --interval=5m --timeout=5s --start-period=30s --retries=3 \
    CMD ["/usr/local/sbin/check-nginx-logs"]
