from flask import Flask, jsonify, request
import psycopg
from psycopg.rows import dict_row

DEFAULT_DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 55432,
    "dbname": "library_db",
    "user": "postgres",
    "password": "secret",
}


def create_app(db_config=None):
    app = Flask(__name__)
    app.config["DB_CONFIG"] = db_config or DEFAULT_DB_CONFIG

    def get_connection():
        return psycopg.connect(
            host=app.config["DB_CONFIG"]["host"],
            port=app.config["DB_CONFIG"]["port"],
            dbname=app.config["DB_CONFIG"]["dbname"],
            user=app.config["DB_CONFIG"]["user"],
            password=app.config["DB_CONFIG"]["password"],
            row_factory=dict_row,
        )

    def init_db():
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS authors (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                birth_year INTEGER
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                genre VARCHAR(100),
                year_published INTEGER,
                author_id INTEGER REFERENCES authors(id) ON DELETE SET NULL,
                created_by VARCHAR(255) NOT NULL
            )
        """)

        conn.commit()
        cur.close()
        conn.close()

    @app.route("/api/authors", methods=["GET"])
    def get_authors():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM authors ORDER BY id")
        authors = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(authors), 200

    @app.route("/api/authors", methods=["POST"])
    def create_author():
        data = request.get_json()

        if not data or not data.get("name"):
            return jsonify({"error": "Field 'name' is required"}), 400

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO authors (name, birth_year)
            VALUES (%s, %s)
            RETURNING *
            """,
            (data.get("name"), data.get("birth_year"))
        )
        author = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(author), 201

    @app.route("/api/authors/<int:author_id>", methods=["GET"])
    def get_author(author_id):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM authors WHERE id = %s", (author_id,))
        author = cur.fetchone()
        cur.close()
        conn.close()

        if not author:
            return jsonify({"error": "Author not found"}), 404

        return jsonify(author), 200

    @app.route("/api/authors/<int:author_id>", methods=["DELETE"])
    def delete_author(author_id):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM authors WHERE id = %s", (author_id,))
        author = cur.fetchone()
        if not author:
            cur.close()
            conn.close()
            return jsonify({"error": "Author not found"}), 404

        cur.execute("DELETE FROM authors WHERE id = %s", (author_id,))
        conn.commit()
        cur.close()
        conn.close()
        return "", 204

    @app.route("/api/authors/<int:author_id>/books", methods=["GET"])
    def get_author_books(author_id):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM authors WHERE id = %s", (author_id,))
        author = cur.fetchone()
        if not author:
            cur.close()
            conn.close()
            return jsonify({"error": "Author not found"}), 404

        cur.execute(
            "SELECT * FROM books WHERE author_id = %s ORDER BY id",
            (author_id,)
        )
        books = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(books), 200

    @app.route("/api/books", methods=["GET"])
    def get_books():
        genre = request.args.get("genre")
        author_id = request.args.get("author_id")
        q = request.args.get("q")

        query = "SELECT * FROM books WHERE 1=1"
        params = []

        if genre:
            query += " AND genre = %s"
            params.append(genre)

        if author_id:
            query += " AND author_id = %s"
            params.append(author_id)

        if q:
            query += " AND LOWER(title) LIKE %s"
            params.append(f"%{q.lower()}%")

        query += " ORDER BY id"

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        books = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(books), 200

    @app.route("/api/books", methods=["POST"])
    def create_book():
        data = request.get_json()

        if not data or not data.get("title"):
            return jsonify({"error": "Field 'title' is required"}), 400

        if not data.get("created_by"):
            return jsonify({"error": "Field 'created_by' is required"}), 400

        author_id = data.get("author_id")

        conn = get_connection()
        cur = conn.cursor()

        if author_id is not None:
            cur.execute("SELECT * FROM authors WHERE id = %s", (author_id,))
            author = cur.fetchone()
            if not author:
                cur.close()
                conn.close()
                return jsonify({"error": "Author does not exist"}), 400

        cur.execute(
            """
            INSERT INTO books (title, genre, year_published, author_id, created_by)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                data.get("title"),
                data.get("genre"),
                data.get("year_published"),
                author_id,
                data.get("created_by"),
            )
        )
        book = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(book), 201

    @app.route("/api/books/<int:book_id>", methods=["GET"])
    def get_book(book_id):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM books WHERE id = %s", (book_id,))
        book = cur.fetchone()
        cur.close()
        conn.close()

        if not book:
            return jsonify({"error": "Book not found"}), 404

        return jsonify(book), 200

    @app.route("/api/books/<int:book_id>", methods=["DELETE"])
    def delete_book(book_id):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM books WHERE id = %s", (book_id,))
        book = cur.fetchone()
        if not book:
            cur.close()
            conn.close()
            return jsonify({"error": "Book not found"}), 404

        cur.execute("DELETE FROM books WHERE id = %s", (book_id,))
        conn.commit()
        cur.close()
        conn.close()
        return "", 204

    with app.app_context():
        init_db()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)