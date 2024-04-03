from db import db


class CRUDModel:
    _db = db
    _cursor = db.cursor
    _tablename = ""

    @classmethod
    async def add(cls, **args):
        keys = args.keys()
        values = args.values()
        keys_tuple = f"({', '.join(keys)})"
        values_tuple = f"({', '.join(['%s' for _ in range(len(values))])})"
        query = f"""
            INSERT INTO {cls.tablename}
            {keys_tuple}
            VALUES
            {values_tuple};
            """
        with cursor() as cursor:
            cursor.execute(query, (*values,))

    @classmethod
    async def get_by_id(cls, id: int, *cols: (str)):
        f_cols = ", ".join(cols)
        query = f"""
            SELECT {f_cols} FROM {cls._tablename}
            WHERE id = %s;"""
        with CRUDModel._cursor() as cursor:
            cursor.execute(query, (id,))
            item = cursor.fetchone()
            return item

    @classmethod
    async def get_all_paginated(cls, offset=0, limit=20):
        print(cls._tablename)
        query = f"""SELECT * FROM {cls._tablename}
            LIMIT %s OFFSET %s;"""
        with CRUDModel._cursor() as cursor:
            cursor.execute(query, (limit, offset))
            items = cursor.fetchall()
            return items

    @classmethod
    async def update_by_id(cls, id, **new_vals):
        keys_tup = ", ".join([f"{key} = %s" for key in new_vals.keys()])
        values_tup = new_vals.values()
        query = f"""
            UPDATE {cls._tablename}
            SET {keys_tup}
            WHERE id = %s"""
        with CRUDModel._cursor() as cursor:
            cursor.execute(
                query,
                (
                    *values_tup,
                    id,
                ),
            )

    @classmethod
    async def delete_by_id(cls, id):
        query = f"""
            DELETE FROM {cls.tablename}
            WHERE id = %s"""
        with CRUDModel._cursor() as cursor:
            cursor.execute(query, (id,))
