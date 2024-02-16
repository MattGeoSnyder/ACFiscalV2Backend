import re
from typing import List
from api import crud_model

crud_model.set_table('departments')


def is_credit(credit):
    return credit['Transaction'] == "ACH Credits"

async def categorize_credit(credit, descriptions, departments):
    department_id = None 
    if credit.get("AccountName"):
        if credit.get("AccountName")[-5:] == "11108":
            kane_dept = departments.filter(lambda dept: dept.name == "Kane")[0]
            department_id = kane_dept.id 
        elif credit.get("AccountName")[-5:] == "11106":
            econ_dept = departments.filter(lambda dept: dept.name == "Economic Development")[0]
            department_id = econ_dept.id
    else:
        for description in descriptions:
            keywords_arr: List[str] = description["keywords_array"]
            keywords = ".*" + ".*".join(keywords_arr) + ".*"
            if re.match(keywords, description):
                department_id = description["department_id"]
    
    return department_id

            

  
    