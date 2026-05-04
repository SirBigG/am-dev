-- Create forum database and grant privileges to existing user 'agr'
-- This script is executed by the official Postgres image at container init
-- It will run only if the Postgres data directory is empty (first initialization).

CREATE DATABASE agroforum OWNER agr;
-- Optional: create a dedicated forum user and grant privileges
-- CREATE USER forum_user WITH PASSWORD 'forum_pass';
-- GRANT ALL PRIVILEGES ON DATABASE agroforum TO forum_user;
