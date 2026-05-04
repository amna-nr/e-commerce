# E-Commerce Backend

Production-ready REST API for an e-commerce store built with FastAPI.

## Stack
FastAPI · PostgreSQL · Redis · JWT · Alembic · Docker

## Features
- JWT authentication with refresh token rotation
- Redis token blacklisting and session invalidation
- Async SQLAlchemy with PostgreSQL
- Alembic database migrations
- Structured JSON logging
- Dockerized with Docker Compose

## Run locally
cp .env.example .env
docker compose up -d

## API Docs
http://localhost:8000/docs
