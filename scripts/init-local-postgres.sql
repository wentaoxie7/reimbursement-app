-- Run in psql or pgAdmin as a superuser (e.g. postgres).
-- Creates the app user/database for local PostgreSQL on port 5432.

CREATE USER reimbursement WITH PASSWORD 'reimbursement';
CREATE DATABASE reimbursement OWNER reimbursement;
GRANT ALL PRIVILEGES ON DATABASE reimbursement TO reimbursement;
