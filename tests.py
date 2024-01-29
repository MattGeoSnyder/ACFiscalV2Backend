import unittest
from dotenv import load_dotenv
from api import CRUDModel
import MySQLdb
import MySQLdb.cursors as Cursors
import os

db = MySQLdb.connect(
    host=os.getenv('TEST_DB_HOST'),
    user=os.getenv("TEST_DB_USERNAME"),
    passwd=os.getenv("TEST_DB_PASSWORD"),
    db=os.getenv("TEST_DB_NAME"),
    autocommit=True,
    cursorclass=Cursors.DictCursor,
)

crud = CRUDModel('departments', db)

class CRUDModelTestForUsers(unittest.TestCase): 
    def tearDown(self) -> None:
        with db.cursor() as cursor:
            cursor.execute('DROP TABLE users')
            cursor.execute("""CREATE TABLE users(
                    id SERIAL PRIMARY KEY,
                    first_name varchar(25) NOT NULL,
                    last_name varchar(25) NOT NULL,
                    email varchar(75) NOT NULL UNIQUE,
                    password text NOT NULL,
                    auth boolean DEFAULT false,
                    department_id integer REFERENCES departments
            )""")

    def test_add(self):
        new_test_user = {'first_name':'Test', 'last_name':'User', 'email':'testuser@test.com', 'password':'test1234', 'department_id':1}
        crud.set_table('users').add(**new_test_user)
        with db.cursor() as cursor: 
            cursor.execute("SELECT * FROM users WHERE email = %s", ('testuser@test.com', ))
            test_user = cursor.fetchone()
            self.assertEqual(test_user, {**test_user, **new_test_user})
