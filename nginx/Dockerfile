FROM nginx

ARG NGINX_CONF

COPY $NGINX_CONF /etc/nginx/nginx.conf
COPY uwsgi_params /etc/nginx/uwsgi_params
