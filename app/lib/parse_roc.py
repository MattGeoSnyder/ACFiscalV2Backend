from fastapi import UploadFile
from csv import reader
from pandas import ExcelFile, read_excel
from pdb import set_trace
from .constants import total_cooridiates, table_start_row_index
from ..models.ROCLineItemModel import NewROCLineItem
from pydantic import BaseModel, ValidationError
import math


async def parse_roc(roc: UploadFile):
    line_items = []

    f = await roc.read()
    df = read_excel(f)
    array = df.values
    trimmed = array[table_start_row_index:]
    print(trimmed)
    for i in range(len(trimmed)):
        if math.isnan(trimmed[i][total_cooridiates[1]]):
            break

        row = trimmed[i][1:]
        print(row)

        line_item = {
            "mcu": row[1],
            "cost_center": str(row[2]),
            "object_number": str(row[3]),
            "subsidiary": str(row[4]) if not math.isnan(row[4]) else None,
            "subledger": str(row[5]) if not math.isnan(row[4]) else None,
            "explanation": str(row[6]),
            "amount_in_cents": math.trunc(row[7] * 100),
        }

        if not NewROCLineItem.model_validate(line_item):
            raise ValidationError("Invalid ROC file")

        line_items.append(line_item)

    return line_items
