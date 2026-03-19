-- ================================================================
-- PORTAL STAE — Script SQL de criacao da base de dados Neon
-- Base de dados: portal_stae
-- Motor: PostgreSQL (via Neon.tech)
-- ================================================================

-- Nota: No Neon.tech a base de dados e criada pela interface web.
-- Este script verifica e configura configuracoes de producao.

-- Configurar encoding
SET client_encoding = 'UTF8';

-- Criar schema padrao (ja existe no Neon, mas por garantia)
CREATE SCHEMA IF NOT EXISTS public;

-- Extensoes uteis para Django
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";     -- UUIDs
CREATE EXTENSION IF NOT EXISTS "pg_trgm";       -- Full-text search trigrams
CREATE EXTENSION IF NOT EXISTS "unaccent";      -- Pesquisa sem acentos (util para pt)

-- Configurar timezone de Mocambique
SET timezone = 'Africa/Maputo';

-- ================================================================
-- CHECKLIST NEON.TECH:
-- ================================================================
-- 1. Aceder a https://neon.tech/
-- 2. Criar conta (gratuita)
-- 3. Criar novo projecto: "portal-stae"
-- 4. Criar base de dados: "portal_stae"
-- 5. Copiar a Connection String
-- 6. Executar: python MIGRAR_PARA_NEON.py --connection "postgresql://..."
-- ================================================================
