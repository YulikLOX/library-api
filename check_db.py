import psycopg

conn = psycopg.connect(
    host="127.0.0.1",
    port=55432,
    dbname="postgres",
    user="postgres",
    password="secret",
)

print("DB OK")
conn.close()