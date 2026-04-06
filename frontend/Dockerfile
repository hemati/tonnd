# Build stage
FROM node:18-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
ARG VITE_GA4_MEASUREMENT_ID
ENV VITE_GA4_MEASUREMENT_ID=$VITE_GA4_MEASUREMENT_ID
RUN npm run build

# Production stage — serve static files with Nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 5173
CMD ["nginx", "-g", "daemon off;"]
