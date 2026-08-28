FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build


FROM nginx:alpine
LABEL org.opencontainers.image.authors="Nils Ost"
COPY --from=build /app/dist/lan-party-onboarding-system /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
