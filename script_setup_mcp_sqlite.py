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
                       price
                       REAL,
                       stock
                       INTEGER
                   )
                   ''')

    products = [
        ('Laptop Pro', 1200.50, 10),
        ('Monitor 4K', 350.00, 25),
        ('Mechanical Keyboard', 89.99, 50)
    ]

    cursor.executemany('INSERT INTO products (name, price, stock) VALUES (?, ?, ?)', products)
    conn.commit()
    conn.close()
    print("Database 'external_data.db' created with test data.")


if __name__ == "__main__":
    create_test_db()