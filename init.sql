CREATE TABLE products (
    code INT UNIQUE,
    product_name VARCHAR(100),
    price FLOAT
)

CREATE TABLE cupons (
    cuponcode VARCHAR(20) UNIQUE,
    discount INT
)

-- Sample data for products
INSERT INTO products (code, product_name, price) VALUES
    (1001, 'Coffee', 3.50),
    (1002, 'Sandwich', 6.00),
    (1003, 'Croissant', 2.75),
    (1004, 'Orange Juice', 3.00),
    (1005, 'Muffin', 2.50),
    (1006, 'Bottled Water', 1.50),
    (1007, 'Bagel', 2.25),
    (1008, 'Iced Tea', 3.25)

-- Sample data for cupons
INSERT INTO cupons (cuponcode, discount) VALUES
    ('SAVE10', 10),
    ('WELCOME20', 20)

