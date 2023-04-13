import psycopg2

conn = psycopg2.connect(
    dbname='flask_db',
    user='postgres',
    password='postgres'
    )

cur = conn.cursor()
cur.execute("ALTER TABLE \"order\" ADD COLUMN being_paid BOOLEAN DEFAULT FALSE;")
conn.commit()

cur.close()
conn.close()
