#!/usr/bin/env python
"""
Script to wait for database to be available before starting Django app.
"""
import os
import sys
import time
import psycopg2
from psycopg2 import OperationalError as Psycopg2OpError

def wait_for_db():
    """Wait for database to be available."""
    db_host = os.getenv('POSTGRES_HOST', 'postgres')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    db_name = os.getenv('POSTGRES_DB', 'aussiz_isms')
    db_user = os.getenv('POSTGRES_USER', 'aussiz_user')
    db_password = os.getenv('POSTGRES_PASSWORD', 'aussiz_password')

    max_retries = 30
    retry_interval = 1  # second

    print(f"Waiting for database at {db_host}:{db_port}...")

    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=db_host,
                port=db_port,
                database=db_name,
                user=db_user,
                password=db_password
            )
            conn.close()
            print("Database is available!")
            return True
        except Psycopg2OpError as e:
            print(f"Database unavailable, waiting {retry_interval} second... ({i+1}/{max_retries})")
            time.sleep(retry_interval)

    print("Could not connect to database after max retries")
    return False

if __name__ == "__main__":
    if not wait_for_db():
        sys.exit(1)