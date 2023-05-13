psql --username postgres -c "CREATE USER logs WITH PASSWORD '$TCK_DB_PASSWORD';"
psql --username postgres -c "CREATE DATABASE logs OWNER logs;"
cat /docker-entrypoint-initdb.d/logs.sql | psql --username logs
