-- =============================================================================
-- Postgres init script — runs once on container first start
-- =============================================================================

-- Required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";     -- fuzzy text matching
CREATE EXTENSION IF NOT EXISTS "unaccent";    -- accent-insensitive FTS

-- Langfuse database (created here so the langfuse container can use the same postgres)
CREATE DATABASE langfuse OWNER rag;

-- Default schema for the RAG app
\c rag
CREATE SCHEMA IF NOT EXISTS rag AUTHORIZATION rag;
