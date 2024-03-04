import re
from typing import List


def is_credit(credit):
    return credit["Transaction"] == "ACH Credits"


def categorize_credit(credit, descriptions):
    department_id = None
    if credit.get("AccountName"):
        if credit.get("AccountName")[-5:] == "11108":
            department_id = 16
        elif credit.get("AccountName")[-5:] == "11106":
            department_id = 9
    else:
        for description in descriptions:
            keywords_arr: List[str] = description["keywords_array"]
            keywords = ".*" + ".*".join(keywords_arr) + ".*"
            if re.match(keywords, description):
                department_id = description["department_id"]

    return department_id
