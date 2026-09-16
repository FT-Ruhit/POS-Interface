import psycopg2
from psycopg2.extras import RealDictCursor


class DB_Connection():
    def __init__(self,table, **kwargs):
        self.conn = psycopg2.connect(**kwargs)
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
        self.table = table
    def fetch_data(self, **kwargs):
        
        column = ", ".join(kwargs.keys())
        placeholder = ", ".join(f"%({key})s" for key in kwargs.keys())
        query = f"SELECT * FROM {self.table} WHERE {column} = {placeholder}"
        self.cur.execute(query, kwargs)
        return self.cur.fetchone()
    
    def fetch_all_data(self):
        self.cur.execute(f"SELECT * FROM {self.table}")
        return self.cur.fetchall()
        
    def push_data(self, **kwargs):
        
        column = ", ".join(kwargs.keys())
        placeholder = ", ".join(f"%({key})s" for key in kwargs.keys())
        query = f"INSERT INTO {self.table} ({column}) VALUES ({placeholder})"
        self.cur.execute(query, kwargs)
        self.conn.commit()
        
    def del_data(self, **kwargs):
        column = ", ".join(kwargs.keys())
        placeholder = ", ".join(f"%({key})s" for key in kwargs.keys())
        query = f"DELETE FROM {self.table} WHERE {column} = {placeholder}"
        self.cur.execute(query, kwargs)
        self.conn.commit()
    
    def close(self):
        self.cur.close()
        self.conn.close()
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc, tb):
        self.close()
        
def main():
    with DB_Connection(
        table = "products",
        host="localhost",
        port=5432,
        dbname="postgres",
        user="postgres",
        password="9123"
    ) as db:
        print(db.fetch_data())
        # db.push_data(
        #     cuponcode = 'HEL30',
        #     discount = 30
        # )
        # db.del_data(
        #     cuponcode = 'HEL30'
        # )
        
if __name__ =="__main__":
    main()

        