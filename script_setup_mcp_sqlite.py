"""
Script to initialize the SQLite database for the Agentic Analyst project.
This script creates the 'external_data.db' file and populates it with sample product data
that serves as a reference for the 'MCP SQLite' tool.

Usage:
    python script_setup_mcp_sqlite.py
"""

import sqlite3
import os

DB_NAME = "external_data.db"

def create_fresh_db():
    """Creates a fresh database, dropping existing tables to ensure a clean state."""
    
    # Remove existing db file if we want a hard reset, or just connect. 
    # Here we just connect and drop the table.
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print(f"Connected to {DB_NAME}...")

    # Drop existing table to avoid duplicates on re-run
    cursor.execute("DROP TABLE IF EXISTS products")
    print("Dropped existing 'products' table (if any).")

    # Create a table for the agent to query
    cursor.execute('''
                   CREATE TABLE products
                   (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       name TEXT NOT NULL,
                       price_in_cents INTEGER NOT NULL,
                       stock INTEGER NOT NULL
                   )
                   ''')
    print("Created 'products' table.")

    # Sample data to verify database interactions
    products = [
        ('Laptop Pro', 120050, 10),       # $1200.50
        ('Monitor 4K', 35000, 25),        # $350.00
        ('Mechanical Keyboard', 8999, 50) # $89.99
    ]

    cursor.executemany('INSERT INTO products (name, price_in_cents, stock) VALUES (?, ?, ?)', products)
    conn.commit()
    print(f"Inserted {len(products)} sample records.")

    conn.close()
    print(f"Database setup complete. File: {os.path.abspath(DB_NAME)}")


if __name__ == "__main__":
    create_fresh_db()