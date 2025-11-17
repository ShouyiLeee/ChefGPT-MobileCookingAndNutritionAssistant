-- Initialize PostgreSQL database with pgvector extension

-- Create pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create pgcrypto extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create pg_trgm extension for fuzzy text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE chefgpt TO postgres;

-- Create indexes for common queries (will be created by Alembic migrations)
-- This file is for initial setup only
