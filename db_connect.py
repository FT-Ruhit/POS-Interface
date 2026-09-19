from init_db import Init_DB


class DB_Connection(Init_DB):
    def __init__(self,table):
        super().__init__()
        self.table = table
    def fetch_data(self, **kwargs):
        if not kwargs:
            raise ValueError("fetch_data() requires at least one condition")
        conditions = " AND ".join(f"{key} = :{key}" for key in kwargs.keys())
        query = f"SELECT * FROM {self.table} WHERE {conditions}"
        self.cur.execute(query, kwargs)
        return self.cur.fetchone()
    
    def fetch_all_data(self):
        self.cur.execute(f"SELECT * FROM {self.table}")
        return self.cur.fetchall()
        
    def push_data(self, **kwargs):
        if not kwargs:
            raise ValueError("push_data() requires at least one column=value pair")
        column = ", ".join(kwargs.keys())
        placeholder = ", ".join(f":{key}" for key in kwargs.keys())
        query = f"INSERT INTO {self.table} ({column}) VALUES ({placeholder})"
        self.cur.execute(query, kwargs)
        self.conn.commit()
        
    def del_data(self, **kwargs):
        if not kwargs:
            raise ValueError("del_data() requires at least one condition")
        conditions = " AND ".join(f"{key} = :{key}" for key in kwargs.keys())
        query = f"DELETE FROM {self.table} WHERE {conditions}"
        self.cur.execute(query, kwargs)
        self.conn.commit()
    
    def close(self):
        self.cur.close()
        self.conn.close()
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc, tb):
        self.conn.close()
        
def main():
    with DB_Connection(
        table = "quickitems"
    ) as db:
        print(db.fetch_all_data())
        # db.push_data(
        #     cuponcode = 'HEL30',
        #     discount = 30
        # )
        # db.del_data(
        #     cuponcode = 'HEL30'
        # )
        
if __name__ =="__main__":
    main()

        