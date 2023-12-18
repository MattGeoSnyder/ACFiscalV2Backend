from db import db
import MySQLdb


class API:
    def __init__(self, db):
        self.db = db
        self.cursor = db.cursor
        self.error = MySQLdb.Error

    def get_all_departments(self):
        with self.cursor() as cursor:
            cursor.execute("SELECT * FROM departments")
            departments = cursor.fetchall()

            return {"departments": departments}

    def get_department_by_id(self, id):
        with self.cursor() as cursor:
            cursor.execute("SELECT * FROM departments WHERE id=%s", (id,))
            department = cursor.fetchone()

            return {"department": department}


API = API(db)
