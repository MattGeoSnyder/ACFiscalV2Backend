from ..db import db


class CRUDModel:
    _db = db
    _cursor = db.cursor
    _tablename = ""

    @property
    def tablename(self):
        return CRUDModel._tablename

    @tablename.setter
    def tablename(self, new_tablename: str):
        self._tablename = new_tablename

    @staticmethod
    async def add(**args):
        keys = args.keys()
        values = args.values()
        keys_tuple = f"({', '.join(keys)})"
        values_tuple = f"({', '.join(['%s' for _ in range(len(values))])})"
        query = f"""
            INSERT INTO {CRUDModel._tablename}
            {keys_tuple}
            VALUES
            {values_tuple};
            """
        with cursor() as cursor:
            cursor.execute(query, (*values,))

    @staticmethod
    async def get_by_id(CRUDModel, id: int, *cols: (str)):
        f_cols = ", ".join(cols)
        query = f"""
            SELECT {f_cols} FROM {CRUDModel._tablename}
            WHERE id = %s;"""
        with cursor() as cursor:
            cursor.execute(query, (id,))
            item = cursor.fetchone()
            return item

    @staticmethod
    async def get_all_paginated(CRUDModel, offset=0, limit=20):
        query = f"""SELECT * FROM {CRUDModel._tablename}
            LIMIT %s OFFSET %s"""
        with cursor() as cursor:
            cursor.execute(query, (limit, offset))
            items = cursor.fetchall()
            return items

    @staticmethod
    async def update_by_id(id, **new_vals):
        keys_tup = ", ".join([f"{key} = %s" for key in new_vals.keys()])
        values_tup = new_vals.values()
        query = f"""
            UPDATE {CRUDModel._tablename}
            SET {keys_tup}
            WHERE id = %s"""
        with cursor() as cursor:
            cursor.execute(
                query,
                (
                    *values_tup,
                    id,
                ),
            )

    @staticmethod
    async def delete_by_id(id):
        query = f"""
            DELETE FROM {CRUDModel._tablename}
            WHERE id = %s"""
        with cursor() as cursor:
            cursor.execute(query, (id,))
