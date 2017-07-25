CREATE DATABASE aiopg;
\c aiopg
CREATE USER aiopg WITH PASSWORD='aiopg';
CREATE TABLE websites ( id serial PRIMARY KEY, url varchar(2050), freq int);
CREATE TABLE crawls ( id serial PRIMARY KEY, date timestamp default now(), url varchar(2050), resp varchar(10485));
GRANT ALL PRIVILEGES on TABLE websites to aiopg;
GRANT ALL PRIVILEGES on TABLE crawls to aiopg;
GRANT USAGE, SELECT ON SEQUENCE websites_id_seq TO aiopg;
GRANT USAGE, SELECT ON SEQUENCE crawls_id_seq TO aiopg;
