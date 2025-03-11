#!/bin/sh

# Wait for PostgreSQL
while ! nc -z $PG_HOST 5432; do sleep 1; done

# Wait for Sybase
while ! nc -z $SYBASE_HOST 1433; do sleep 1; done

# Initialize database
python /app/scripts/init_db.py

# Start main service
exec "$@"