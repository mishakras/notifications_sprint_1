FROM nginx:1.26.3

COPY ./nginx/nginx.conf /etc/nginx/nginx.conf
COPY ./frontend /app/frontend_service/frontend

RUN chmod -R 755 /app/
