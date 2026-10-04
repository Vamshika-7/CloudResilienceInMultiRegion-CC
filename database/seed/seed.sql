-- Seed data for products table

INSERT INTO products (name, description, price, stock)
VALUES 
    ('Cloud Ultra Laptop 15', 'High-performance 16-core laptop optimized for distributed systems engineers and developers.', 1299.99, 25),
    ('Noise-Canceling Wireless Headphones', 'Active noise cancellation with 40-hour battery life and spatial audio support.', 199.50, 50),
    ('Mechanical Tactile Keyboard', 'Custom RGB backlit keyboard with hot-swappable switches and PBT keycaps.', 89.99, 75),
    ('4K HDR Professional Monitor', '27-inch IPS panel with 99% sRGB color gamut and 90W USB-C power delivery.', 399.00, 30),
    ('Ergonomic Precision Mouse', 'Wireless dual-mode connectivity with customizable DPI and thumb scroll wheel.', 49.99, 100),
    ('USB-C Dual 4K Docking Station', 'Thunderbolt-compatible dock with dual HDMI, Gigabit Ethernet, and 100W PD.', 129.00, 40)
ON CONFLICT DO NOTHING;
