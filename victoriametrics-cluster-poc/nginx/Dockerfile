FROM nginx:alpine

# openssl for dummy self-signed cert generation
RUN apk add --no-cache openssl

# Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Static site
COPY index.html /usr/share/nginx/html/index.html
COPY south-park.html /usr/share/nginx/html/south-park.html
COPY images/ /usr/share/nginx/html/images/

# Custom entrypoint
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
