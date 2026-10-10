# Serves the Flutter web build on Cloud Run. The build context is deploy/cloudrun with build/web copied to ./web.
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY web /usr/share/nginx/html
ENV PORT=8080
EXPOSE 8080
