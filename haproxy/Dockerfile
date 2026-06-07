FROM haproxytech/haproxy-alpine:2.9.6
COPY ./services.lua /usr/local/etc/haproxy/services.lua
COPY ./haproxy.cfg /usr/local/etc/haproxy/haproxy.cfg
EXPOSE 80/tcp 443/tcp 8404/tcp 5555/tcp
