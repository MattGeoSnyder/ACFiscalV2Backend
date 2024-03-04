from ..db import db


class CRUDModel:
    def __init__(self, tablename: str, db):
        self.tablename = tablename
        self.db = db
        self.cursor = db.cursor

    @staticmethod
    def set_table(self, tablename):
        self.tablename = tablename
        return self

    @staticmethod
    async def add(self, **args):
        keys = args.keys()
        values = args.values()
        keys_tuple = f"({', '.join(keys)})"
        values_tuple = f"({', '.join(['%s' for _ in range(len(values))])})"
        query = f"""
            INSERT INTO {self.tablename}
            {keys_tuple}
            VALUES
            {values_tuple};
            """
        with self.cursor() as cursor:
            cursor.execute(query, (*values,))

    @staticmethod
    async def get_by_id(self, id: int, *cols: (str)):
        f_cols = ", ".join(cols)
        query = f"""
            SELECT {f_cols} FROM {self.tablename}
            WHERE id = %s;"""
        with self.cursor() as cursor:
            cursor.execute(query, (id,))
            item = cursor.fetchone()
            return item

    @staticmethod
    async def get_all_paginated(self, offset=0, limit=20):
        query = f"""SELECT * FROM {self.tablename}
            LIMIT %s OFFSET %s"""
        with self.cursor() as cursor:
            cursor.execute(query, (limit, offset))
            items = cursor.fetchall()
            return items

    @staticmethod
    async def update_by_id(self, id, **new_vals):
        keys_tup = ", ".join([f"{key} = %s" for key in new_vals.keys()])
        values_tup = new_vals.values()
        query = f"""
            UPDATE {self.tablename}
            SET {keys_tup}
            WHERE id = %s"""
        with self.cursor() as cursor:
            cursor.execute(
                query,
                (
                    *values_tup,
                    id,
                ),
            )

    @staticmethod
    async def delete_by_id(self, id):
        query = f"""
            DELETE FROM {self.tablename}
            WHERE id = %s"""
        with self.cursor() as cursor:
            cursor.execute(query, (id,))
