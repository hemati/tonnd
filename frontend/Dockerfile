# Build stage
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
ARG VITE_API_ENDPOINT
ARG VITE_GA4_MEASUREMENT_ID
ENV VITE_API_ENDPOINT=$VITE_API_ENDPOINT
ENV VITE_GA4_MEASUREMENT_ID=$VITE_GA4_MEASUREMENT_ID
RUN apk add --no-cache chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser
RUN npm run build

# Production stage — serve static files with Nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 5173
CMD ["nginx", "-g", "daemon off;"]
