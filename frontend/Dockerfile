FROM node:22-alpine AS build

WORKDIR /app

COPY package*.json ./

RUN npm ci

COPY . .

RUN npm run build

# Stage chạy thực tế với Nginx
FROM nginx:alpine AS runtime

WORKDIR /usr/share/nginx/html

COPY --from=build /app/dist ./

# Cấu hình Nginx proxy /api sang backend Django
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]


