INSERT INTO categories (id, name) VALUES
    (1, 'Laptops'),
    (2, 'Accessories'),
    (3, 'Monitors'),
    (4, 'Audio'),
    (5, 'Networking'),
    (6, 'Storage');

INSERT INTO products (id, name, category_id, price, stock) VALUES
    (1, 'Laptop Pro 14', 1, 999.99, 12),
    (2, 'Laptop Air 13', 1, 799.99, 8),
    (3, 'Wireless Mouse', 2, 24.99, 24),
    (4, 'Mechanical Keyboard', 2, 89.99, 15),
    (5, 'USB-C Dock', 2, 129.99, 10),
    (6, 'USB-C Monitor 27', 3, 249.99, 7),
    (7, 'UltraWide Monitor 34', 3, 499.99, 4),
    (8, 'Noise Cancelling Headphones', 4, 179.99, 11),
    (9, 'USB Microphone', 4, 99.99, 6),
    (10, 'Wi-Fi 6 Router', 5, 149.99, 9),
    (11, 'External SSD 1TB', 6, 119.99, 18),
    (12, 'Portable HDD 2TB', 6, 74.99, 13);

INSERT INTO orders (id, customer_name, status, total_amount, created_at) VALUES
    (1, 'Default Customer', 'confirmed', 49.98, '2026-09-20 10:15:00'),
    (2, 'Default Customer', 'confirmed', 249.99, '2026-09-22 14:30:00');

INSERT INTO order_items (order_id, product_id, quantity, unit_price, line_total) VALUES
    (1, 3, 2, 24.99, 49.98),
    (2, 6, 1, 249.99, 249.99);
