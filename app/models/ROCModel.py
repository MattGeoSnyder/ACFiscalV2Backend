from .CRUDModel import CRUDModel
from pydantic import BaseModel, Field


class NewROC(BaseModel):
    filename: str
    roc: bytes
    amount_in_cents: int
    # TODO: Need to change default value

    user_id: int = Field(1)


class ROCModel(CRUDModel):
    _tablename = "rocs"

    def __init__(self):
        super().__init__()

    @staticmethod
    async def post_roc(roc, user_id):
        with cursor() as cursor:
            cursor.execute(
                """
                    INSERT INTO rocs
                    (user_id, file_path)
                    VALUES
                    (%s, %s);
                """,
                (user_id, roc.filename),
            )
            roc_id = cursor.lastrowid
            return roc_id