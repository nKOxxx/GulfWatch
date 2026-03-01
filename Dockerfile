FROM node:20-alpine AS backend-build

WORKDIR /app/backend
COPY backend/package*.json ./
RUN npm ci
COPY backend/ ./
RUN npm run build

FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM node:20-alpine

WORKDIR /app

# Copy backend
COPY --from=backend-build /app/backend/dist ./dist
COPY --from=backend-build /app/backend/node_modules ./node_modules
COPY --from=backend-build /app/backend/package*.json ./

# Copy frontend
COPY --from=frontend-build /app/frontend/dist ./public

EXPOSE 3001

CMD ["node", "dist/index.js"]
