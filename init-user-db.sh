mv /docker-entrypoint-initdb.d/pg_hba.conf /var/lib/postgresql/data
psql --username postgres -c "CREATE USER logs WITH PASSWORD '$DB_PASSWORD';"
psql --username postgres -c "CREATE DATABASE logs OWNER logs;"
cat /docker-entrypoint-initdb.d/logs.sql | psql --username logs
