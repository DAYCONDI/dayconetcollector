-- DaycoNet database and roles setup.
-- Passwords are passed via psql variables, NOT stored in this file.
-- Run via scripts\setup_db.bat, or manually:
--   psql -U postgres -v writer_pw='secret1' -v reader_pw='secret2' -f scripts\create_db.sql
-- Idempotent: safe to run more than once.

-- Create dayconet_writer if missing.
SELECT format('CREATE ROLE dayconet_writer LOGIN PASSWORD %L', :'writer_pw')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'dayconet_writer')
\gexec

-- Always set dayconet_writer password (role now definitely exists).
SELECT format('ALTER ROLE dayconet_writer WITH LOGIN PASSWORD %L', :'writer_pw')
\gexec

-- Create dayconet_reader if missing.
SELECT format('CREATE ROLE dayconet_reader LOGIN PASSWORD %L', :'reader_pw')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'dayconet_reader')
\gexec

-- Always set dayconet_reader password (role now definitely exists).
SELECT format('ALTER ROLE dayconet_reader WITH LOGIN PASSWORD %L', :'reader_pw')
\gexec

-- Create database if missing.
SELECT 'CREATE DATABASE dayconet OWNER dayconet_writer'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'dayconet')
\gexec

\connect dayconet

GRANT CONNECT ON DATABASE dayconet TO dayconet_writer, dayconet_reader;
GRANT USAGE ON SCHEMA public TO dayconet_writer, dayconet_reader;
