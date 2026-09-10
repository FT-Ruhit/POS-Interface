import psycopg2
from psycopg2.extras import RealDictCursor


class DB_Connection():
    def __init__(self,table, **kwargs):
        self.conn = psycopg2.connect(**kwargs)
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
        self.table = table
    def fetch_data(self):
        self.cur.execute(f"SELECT * FROM {self.table}")
        return self.cur.fetchall()
        # data = []
        # for row in rows:
        #     data.append(dict(row))
        # return data
    
    def close(self):
        self.cur.close()
        self.conn.close()
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc, tb):
        self.close()
        
def main():
    with DB_Connection(
        table = "cupons",
        host="localhost",
        port=5432,
        dbname="postgres",
        user="postgres",
        password="9123"
    ) as db:
        print(db.fetch_data())
        
if __name__ =="__main__":
    main()

        