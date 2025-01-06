
import sqlite3

def init_db():
    conn = sqlite3.connect("static/database/bugbox.db")
    c = conn.cursor()
    # Drop tables if they exist
    c.execute("DROP TABLE IF EXISTS users")
    # Recreate tables
    c.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)
    # Insert a couple of default users
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", "SuperSecurePa$$W0rd123!"))
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("test", "test123"))
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("carlos", "carlos123"))
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("itamar", "basketball_is_life"))
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("marco", "polo"))
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("lebron ", "lebron123"))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database reset initialized!")

