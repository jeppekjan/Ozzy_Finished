import cs50

# Initialize the database
db = cs50.SQL("sqlite:///ozzy.db")

# Table 1: User Table
db.execute("""
CREATE TABLE IF NOT EXISTS bruger (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Email TEXT NOT NULL,
    Password TEXT NOT NULL,
    Username TEXT NOT NULL
)
""")



# Table 4: User List Table
db.execute("""
CREATE TABLE IF NOT EXISTS Ulist (
    ID_U INTEGER PRIMARY KEY AUTOINCREMENT,
    Product_name TEXT NOT NULL,
    Grams INTEGER NOT NULL
)
""")

# Table 5: Food Products Table
db.execute("""
CREATE TABLE IF NOT EXISTS Food_product (
    ID_fp INTEGER PRIMARY KEY AUTOINCREMENT,
    ID_Ra TEXT NOT NULL,
    Navn TEXT NOT NULL,
    CO2 INTEGER,
    Energi INTEGER NOT NULL,
    Fedt INTEGER NOT NULL,
    Kulhydrat INTEGER NOT NULL,
    Protein INTEGER NOT NULL
)
""")


db.execute("""
CREATE TABLE IF NOT EXISTS Processed_Files (
    file_name TEXT PRIMARY KEY
)
""")

db.execute("""
CREATE TABLE IF NOT EXISTS UserFoodLog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_name TEXT,
    grams INTEGER,
    rCO2 INTEGER,
    rEnergi INTEGER NOT NULL,
    rFedt INTEGER NOT NULL,
    rKulhydrat INTEGER NOT NULL,
    rProtein INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")


print("All tables have been created successfully.")
