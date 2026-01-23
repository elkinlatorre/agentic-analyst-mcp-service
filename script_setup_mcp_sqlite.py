import sqlite3


def create_test_db():
    conn = sqlite3.connect("external_data.db")
    cursor = conn.cursor()

    # Create a table for the agent to query
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS products
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY,
                       name
                       TEXT,
                       price_in_cents
                       INTEGER,
                       stock
                       INTEGER
                   )
                   ''')

    products = [
        ('Laptop Pro', 120050, 10),
        ('Monitor 4K', 35000, 25),
        ('Mechanical Keyboard', 8999, 50)
    ]

    cursor.executemany('INSERT INTO products (name, price_in_cents, stock) VALUES (?, ?, ?)', products)
    conn.commit()
    conn.close()
    print("Database 'external_data.db' created with test data.")


if __name__ == "__main__":
    create_test_db()