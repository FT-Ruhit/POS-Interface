import sqlite3

class Init_DB:
    def __init__(self):
        self.conn = sqlite3.connect("Data.db")
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self.define_table()

    def define_table(self):
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                code INT UNIQUE,
                product_name VARCHAR(100),
                price FLOAT
            )   
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS cupons (
                cuponcode VARCHAR(20) UNIQUE,
                discount INT
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS quickitems (
                product_name VARCHAR(100),
                price FLOAT
            )    
        """)
        self.conn.commit()
    def add_test_data(self):
        self.cur.execute("""
            INSERT INTO products (code, product_name, price) VALUES
                (1001, 'Coffee', 3.50),
                (1002, 'Sandwich', 6.00),
                (1003, 'Croissant', 2.75),
                (1004, 'Orange Juice', 3.00),
                (1005, 'Muffin', 2.50),
                (1006, 'Bottled Water', 1.50),
                (1007, 'Bagel', 2.25),
                (1008, 'Iced Tea', 3.25)
        """)
        self.cur.execute("""
            INSERT INTO cupons (cuponcode, discount) VALUES
                ('SAVE10', 10),
                ('WELCOME20', 20)
        """)
        self.cur.execute("""
            INSERT INTO quickitems (product_name, price) VALUES
                ('Coffee', 3.50),
                ('Orange Juice', 3.00),
                ('Bottled Water', 1.50),
                ('Iced Tea', 3.25)
        """)
        self.conn.commit()
        
def main():
    a = Init_DB()
    # a.add_test_data()
    print(a.fetch_all_data())
    
if __name__ == "__main__":
    main()