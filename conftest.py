import os
import pytest
import psycopg2
from app import create_app

TEST_DB_CONFIG = {
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": int(os.environ.get("POSTGRES_PORT", "5432")),
    "database": os.environ.get("POSTGRES_DB", "library_test_db"),
    "user": os.environ.get("POSTGRES_USER", "postgres"),
    "password": os.environ.get("POSTGRES_PASSWORD", "secret"),
}

import pytest
import psycopg
from app import create_app

ADMIN_DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "postgres",
    "user": "postgres",
    "password": "secret",
}

TEST_DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "library_test_db",
    "user": "postgres",
    "password": "secret",
}


@pytest.fixture(scope="session")
def test_db():
    admin_conn = psycopg.connect(
        host=ADMIN_DB_CONFIG["host"],
        port=ADMIN_DB_CONFIG["port"],
        dbname=ADMIN_DB_CONFIG["dbname"],
        user=ADMIN_DB_CONFIG["user"],
        password=ADMIN_DB_CONFIG["password"],
        autocommit=True,
    )
    admin_cur = admin_conn.cursor()

    admin_cur.execute("DROP DATABASE IF EXISTS library_test_db")
    admin_cur.execute("CREATE DATABASE library_test_db")

    admin_cur.close()
    admin_conn.close()

    yield TEST_DB_CONFIG

    admin_conn = psycopg.connect(
        host=ADMIN_DB_CONFIG["host"],
        port=ADMIN_DB_CONFIG["port"],
        dbname=ADMIN_DB_CONFIG["dbname"],
        user=ADMIN_DB_CONFIG["user"],
        password=ADMIN_DB_CONFIG["password"],
        autocommit=True,
    )
    admin_cur = admin_conn.cursor()
    admin_cur.execute("DROP DATABASE IF EXISTS library_test_db")
    admin_cur.close()
    admin_conn.close()


@pytest.fixture(scope="session")
def app(test_db):
    app = create_app(test_db)
    app.config["TESTING"] = True
    return app


@pytest.fixture(scope="function")
def client(app):
    conn = psycopg.connect(
        host=app.config["DB_CONFIG"]["host"],
        port=app.config["DB_CONFIG"]["port"],
        dbname=app.config["DB_CONFIG"]["dbname"],
        user=app.config["DB_CONFIG"]["user"],
        password=app.config["DB_CONFIG"]["password"],
        autocommit=True,
    )
    cur = conn.cursor()
    cur.execute("TRUNCATE books, authors RESTART IDENTITY CASCADE")
    cur.close()
    conn.close()

    with app.test_client() as client:
        yield client