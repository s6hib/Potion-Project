-- create the global_inventory table if it doesn't exist
CREATE TABLE IF NOT EXISTS global_inventory (
    id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    gold INTEGER NOT NULL DEFAULT 100
);

-- create the potion_types table
CREATE TABLE IF NOT EXISTS potion_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    sku VARCHAR NOT NULL UNIQUE,
    red INTEGER NOT NULL,
    green INTEGER NOT NULL,
    blue INTEGER NOT NULL,
    dark INTEGER NOT NULL,
    price INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0
);

-- add constraints to potion_types table
ALTER TABLE potion_types
ADD CONSTRAINT check_color_range CHECK (red >= 0 AND red <= 100 AND green >= 0 AND green <= 100 AND blue >= 0 AND blue <= 100 AND dark >= 0 AND dark <= 100),
ADD CONSTRAINT check_color_sum CHECK (red + green + blue + dark = 100),
ADD CONSTRAINT check_positive_price CHECK (price > 0),
ADD CONSTRAINT check_non_negative_quantity CHECK (quantity >= 0);

-- create the carts table
CREATE TABLE IF NOT EXISTS carts (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR NOT NULL,
    character_class VARCHAR NOT NULL,
    level INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- create the cart_items table
CREATE TABLE IF NOT EXISTS cart_items (
    id SERIAL PRIMARY KEY,
    cart_id INTEGER REFERENCES carts(id),
    potion_type_id INTEGER REFERENCES potion_types(id),
    quantity INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- add constraint to cart_items table
ALTER TABLE cart_items
ADD CONSTRAINT check_positive_quantity CHECK (quantity > 0);

-- insert some initial potion types
INSERT INTO potion_types (name, sku, red, green, blue, dark, price) VALUES
('Red Potion', 'RED_POTION', 100, 0, 0, 0, 50),
('Green Potion', 'GREEN_POTION', 0, 100, 0, 0, 50),
('Blue Potion', 'BLUE_POTION', 0, 0, 100, 0, 50),
('Purple Potion', 'PURPLE_POTION', 50, 0, 50, 0, 75);

-- initialize the global_inventory
INSERT INTO global_inventory (id, gold) VALUES (1, 100) ON CONFLICT (id) DO UPDATE SET gold = 100;
