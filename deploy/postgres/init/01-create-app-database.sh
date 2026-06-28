#!/bin/sh
set -eu

: "${CINEDIVE_DB:?CINEDIVE_DB is required}"
: "${CINEDIVE_APP_USER:?CINEDIVE_APP_USER is required}"
: "${CINEDIVE_APP_PASSWORD:?CINEDIVE_APP_PASSWORD is required}"

psql \
  -v ON_ERROR_STOP=1 \
  -v app_user="$CINEDIVE_APP_USER" \
  -v app_password="$CINEDIVE_APP_PASSWORD" \
  --username "$POSTGRES_USER" \
  --dbname postgres <<-'EOSQL'
SELECT format(
    'CREATE ROLE %I LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION',
    :'app_user',
    :'app_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = :'app_user') \gexec

SELECT format(
    'ALTER ROLE %I WITH LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION',
    :'app_user',
    :'app_password') \gexec
EOSQL

psql \
  -v ON_ERROR_STOP=1 \
  -v app_db="$CINEDIVE_DB" \
  -v app_user="$CINEDIVE_APP_USER" \
  --username "$POSTGRES_USER" \
  --dbname postgres <<-'EOSQL'
SELECT format('CREATE DATABASE %I OWNER %I', :'app_db', :'app_user')
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = :'app_db') \gexec
EOSQL

psql \
  -v ON_ERROR_STOP=1 \
  -v app_db="$CINEDIVE_DB" \
  -v app_user="$CINEDIVE_APP_USER" \
  --username "$POSTGRES_USER" \
  --dbname "$CINEDIVE_DB" <<-'EOSQL'
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
SELECT format('GRANT CONNECT ON DATABASE %I TO %I', :'app_db', :'app_user') \gexec
SELECT format('GRANT CREATE, USAGE ON SCHEMA public TO %I', :'app_user') \gexec
EOSQL
