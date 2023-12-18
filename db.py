from dotenv import load_dotenv

load_dotenv()
import os
import MySQLdb
import MySQLdb.cursors as Cursors

db = MySQLdb.connect(
    host=os.getenv("DATABASE_HOST"),
    user=os.getenv("DATABASE_USERNAME"),
    passwd=os.getenv("DATABASE_PASSWORD"),
    db=os.getenv("DATABASE"),
    autocommit=True,
    ssl_mode="VERIFY_IDENTITY",
    ssl={"ca": "/etc/ssl/certs/ca-certificates.crt"},
    cursorclass=Cursors.DictCursor,
)

try:
    cursor = db.cursor()

    cursor.execute("SHOW TABLES")

    tables = cursor.fetchall()
    for table in tables:
        print("Table:", table["Tables_in_acfiscal"])

except MySQLdb.Error as e:
    print("MySQL Error:", e)

finally:
    cursor.close()
