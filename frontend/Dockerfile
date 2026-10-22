# ============================================================
# STAGE 1: Development
# ============================================================
FROM node:20-alpine AS development

WORKDIR /app

# Install deps
COPY package*.json ./
RUN npm install

# Copy source
COPY . .

EXPOSE 3000

CMD ["npm", "start"]

# ============================================================
# STAGE 2: Build (for production)
# ============================================================
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# ============================================================
# STAGE 3: Production (Nginx)
# ============================================================
FROM nginx:alpine AS production

# Copy built app
COPY --from=build /app/build /usr/share/nginx/html

# Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]