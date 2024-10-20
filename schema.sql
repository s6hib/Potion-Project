-- Custom Potion Types Table
CREATE TABLE potion_types (
    id SERIAL PRIMARY KEY,
    red_ml INTEGER NOT NULL,
    green_ml INTEGER NOT NULL,
    blue_ml INTEGER NOT NULL,
    dark_ml INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    price INTEGER NOT NULL,
    inventory INTEGER NOT NULL DEFAULT 0
);

-- Insert some initial potion types
INSERT INTO potion_types (red_ml, green_ml, blue_ml, dark_ml, name, price) VALUES
(100, 0, 0, 0, 'RED_POTION_0', 50),
(0, 100, 0, 0, 'GREEN_POTION_0', 50),
(0, 0, 100, 0, 'BLUE_POTION_0', 50),
(50, 50, 0, 0, 'YELLOW_POTION_0', 75),
(50, 0, 50, 0, 'PURPLE_POTION_0', 75),
(0, 50, 50, 0, 'CYAN_POTION_0', 75);

-- Carts Table
CREATE TABLE carts (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    character_class VARCHAR(255) NOT NULL,
    level INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cart Items Table
CREATE TABLE cart_items (
    id SERIAL PRIMARY KEY,
    cart_id INTEGER REFERENCES carts(id),
    potion_type_id INTEGER REFERENCES potion_types(id),
    quantity INTEGER NOT NULL,
    UNIQUE(cart_id, potion_type_id)
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

-- Shop Capacity Table
CREATE TABLE shop_capacity (
    id INTEGER PRIMARY KEY DEFAULT 1,
    potion_capacity INTEGER NOT NULL DEFAULT 1,
    ml_capacity INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT single_row CHECK (id = 1)
);

-- Insert initial shop capacity
INSERT INTO shop_capacity (potion_capacity, ml_capacity) VALUES (1, 1);

-- Comments explaining each table's purpose
COMMENT ON TABLE potion_types IS 'Stores information about different potion types, their composition, and inventory.';
COMMENT ON TABLE carts IS 'Represents customer carts with customer information.';
COMMENT ON TABLE cart_items IS 'Stores items added to customer carts. Gets cleared out when someone checks out.';
COMMENT ON TABLE inventory IS 'Tracks the overall inventory of liquid colors and gold.';
COMMENT ON TABLE shop_capacity IS 'Tracks the current capacity for potions and ml in the shop.';
