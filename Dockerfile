# Stage 1: Build Frontend
FROM node:20-alpine AS build-stage
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend .
RUN npm run build

# Stage 2: Run Python Backend
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc g++ libpq-dev && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --default-timeout=100 -r requirements.txt

# Copy backend files
COPY . .

# Copy built frontend assets from stage 1
COPY --from=build-stage /frontend/dist /app/dist

# Expose port and run FastAPI
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
