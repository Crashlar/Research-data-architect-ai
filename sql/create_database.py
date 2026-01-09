import sqlite3
import os

connection = sqlite3.connect("company.db")
cursor = connection.cursor()

if not os.path.exists("company.db"):
    # Create tables
    schema = """
    CREATE TABLE IF NOT EXISTS employees (
        employee_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name     TEXT NOT NULL,
        role          TEXT NOT NULL,
        department    TEXT NOT NULL,
        salary        REAL NOT NULL CHECK (salary >= 0),
        hired_at      DATE NOT NULL DEFAULT CURRENT_DATE,
        is_active     INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS users (
        user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name     TEXT NOT NULL,
        email         TEXT UNIQUE NOT NULL,
        created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS products (
        product_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name  TEXT NOT NULL,
        category      TEXT NOT NULL,
        price         REAL NOT NULL CHECK (price >= 0),
        sku           TEXT UNIQUE,
        is_active     INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS purchases (
        purchase_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id       INTEGER NOT NULL,
        product_id    INTEGER NOT NULL,
        quantity      INTEGER NOT NULL CHECK (quantity > 0),
        total_amount  REAL NOT NULL CHECK (total_amount >= 0),
        purchased_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY(product_id) REFERENCES products(product_id) ON DELETE RESTRICT
    );
    """
    cursor.executescript(schema)

    # Insert sample data
    cursor.executescript("""
    INSERT INTO employees (full_name, role, department, salary, hired_at, is_active) VALUES
    ('Asha Verma', 'Senior Developer', 'Engineering', 1550000, '2022-03-10', 1),
    ('Rohit Singh', 'Data Analyst', 'Data', 900000, '2023-07-01', 1),
    ('Meera Iyer', 'HR Manager', 'HR', 1100000, '2021-11-18', 1),
    ('Kabir Khan', 'QA Engineer', 'Engineering', 800000, '2024-02-05', 1),
    ('Neha Gupta', 'Support Lead', 'Support', 700000, '2020-09-22', 0);

    INSERT INTO users (full_name, email, created_at) VALUES
    ('Ankit Sharma', 'ankit@example.com', '2024-08-10 10:00:00'),
    ('Priya Nair', 'priya@example.com', '2024-09-05 12:30:00'),
    ('Rahul Mehta', 'rahul@example.com', '2024-10-01 09:15:00'),
    ('Sana Khan', 'sana@example.com', '2024-10-15 18:45:00'),
    ('Vikram Patel', 'vikram@example.com', '2024-11-02 14:20:00');

    INSERT INTO products (product_name, category, price, sku, is_active) VALUES
    ('White T-shirt', 'Apparel', 499, 'WT-001', 1),
    ('Blue Jeans', 'Apparel', 1299, 'BJ-101', 1),
    ('Sneakers', 'Footwear', 2999, 'SN-450', 1),
    ('Black Hoodie', 'Apparel', 1999, 'BH-220', 1),
    ('Analog Watch', 'Accessories', 3499, 'AW-777', 1);

    INSERT INTO purchases (user_id, product_id, quantity, total_amount, purchased_at) VALUES
    (1, 1, 2, 998, '2024-11-12 11:00:00'),
    (2, 2, 1, 1299, '2024-11-13 09:30:00'),
    (3, 1, 1, 499, '2024-11-15 16:20:00'),
    (3, 5, 1, 3499, '2024-11-18 10:05:00'),
    (4, 3, 1, 2999, '2024-11-20 19:00:00'),
    (5, 4, 1, 1999, '2024-11-21 08:40:00'),
    (2, 1, 3, 1497, '2024-11-22 12:10:00');
    """)
    print("Database created and sample data inserted.")
else:
    print("Database already exists. Skipping schema and sample data insertion.")


connection.commit()
connection.close()