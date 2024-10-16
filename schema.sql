-- Custom Potion Types Table
CREATE TABLE potion_types (
    id SERIAL PRIMARY KEY,
    red_ml INTEGER NOT NULL,
    green_ml INTEGER NOT NULL,
    blue_ml INTEGER NOT NULL,
    dark_ml INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    inventory INTEGER NOT NULL DEFAULT 0
);

-- Insert some initial potion types
INSERT INTO potion_types (red_ml, green_ml, blue_ml, dark_ml, name, price) VALUES
(100, 0, 0, 0, 'Pure Red Potion', 10.00),
(0, 100, 0, 0, 'Pure Green Potion', 10.00),
(0, 0, 100, 0, 'Pure Blue Potion', 10.00),
(50, 50, 0, 0, 'Yellow Potion', 15.00),
(50, 0, 50, 0, 'Purple Potion', 15.00),
(0, 50, 50, 0, 'Cyan Potion', 15.00);

-- Carts Table
CREATE TABLE carts (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cart Items Table
CREATE TABLE cart_items (
    id SERIAL PRIMARY KEY,
    cart_id INTEGER REFERENCES carts(id),
    potion_type_id INTEGER REFERENCES potion_types(id),
    quantity INTEGER NOT NULL
);

-- Inventory Table
CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    red_ml INTEGER NOT NULL DEFAULT 0,
    green_ml INTEGER NOT NULL DEFAULT 0,
    blue_ml INTEGER NOT NULL DEFAULT 0,
    dark_ml INTEGER NOT NULL DEFAULT 0,
    gold INTEGER NOT NULL DEFAULT 100
);

-- Insert initial inventory
INSERT INTO inventory (red_ml, green_ml, blue_ml, dark_ml, gold) VALUES (0, 0, 0, 0, 100);

-- Comments explaining each table's purpose
COMMENT ON TABLE potion_types IS 'Stores information about different potion types, their composition, and inventory';
COMMENT ON TABLE carts IS 'Represents customer carts';
COMMENT ON TABLE cart_items IS 'Stores items added to customer carts';
COMMENT ON TABLE inventory IS 'Tracks the overall inventory of liquid colors and gold';
