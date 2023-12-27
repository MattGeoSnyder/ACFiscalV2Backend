from fastapi import HTTPException, Depends, UploadFile
from db import db
import MySQLdb
from passlib.context import CryptContext
from jose import JWTError, jwt
from typing import Dict, List
from dotenv import load_dotenv
import os
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from models import User, NewAchCredit
import json
from ach import categorize_credit 
import csv
import pdb
import io
import math
from datetime import date

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str):
    return pwd_context.hash(password)


def create_access_token(data: Dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(
        to_encode, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM")
    )
    return encoded_jwt


def authenticate_user(email: str, password: str):
    user = API.get_user_by_email(email).get("user")
    if not user:
        return False
    if not verify_password(password, user.get("password")):
        return False
    return user


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), os.getenv("ALGORITHM"))
        email: str = payload.get("email")
        if email is None:
            raise HTTPException(401, "Unauthorized")
    except JWTError:
        raise HTTPException(401, "Unauthorized")
    user = API.get_user_by_id(payload.get("id"))
    if user is None:
        raise HTTPException(401, "Unauthorized")
    return user


class API:
    def __init__(self, db):
        self.db = db
        self.cursor = db.cursor
        self.error = MySQLdb.Error

    async def signup(self, user):
        # with self.cursor() as cursor:
        #     cursor.execute(
        #         """
        #             SELECT * FROM users
        #             WHERE email = %s;
        #         """,
        #         (user["email"],),
        #     )

        #     existing_user = cursor.fetchone()
        existing_user = self.get_user_by_id(user.get("id"))

        if existing_user:
            raise HTTPException(
                409, f"Account already registered with email {user['email']}"
            )

        hashed_password = get_password_hash(user["password"])
        new_user = {**user, "password": hashed_password}

        with self.cursor() as cursor:
            cursor.execute(
                """
                    INSERT INTO users
                    (first_name, last_name, email, password, department_id)
                    VALUES
                    (%s, %s, %s, %s, %s);
                """,
                new_user.values(),
            )

            return {"msg": "User successfully created!"}

    async def verify_token(self, form_data):
        user = API.get_user_by_email(form_data.get("email"))
        if not User:
            raise HTTPException(401, "Unauthorized")
        token = create_access_token(
            data={
                "id": user.get("id"),
                "email": user.get("email"),
                "department_id": user.get("department_id"),
            }
        )
        return token

    async def get_all_departments(self):
        with self.cursor() as cursor:
            cursor.execute("SELECT * FROM departments")
            departments = cursor.fetchall()

            return departments

    async def get_department_by_id(self, id: int):
        with self.cursor() as cursor:
            cursor.execute("SELECT * FROM departments WHERE id=%s", (id,))
            department = cursor.fetchone()

            return department

    async def get_all_users(self) -> List[User]:
        with self.cursor() as cursor:
            cursor.execute(
                "SELECT id, email, first_name, last_name, department_id FROM users;"
            )

            users = cursor.fetchall()
            return users

    async def get_user_by_id(self, id: int):
        with self.cursor() as cursor:
            cursor.execute(
                "SELECT id, email, first_name, last_name, department_id FROM users WHERE id = %s;",
                (id,),
            )
            user = cursor.fetchone()

            return user

    async def get_user_by_email(self, email: str):
        with self.cursor() as cursor:
            cursor.execute(
                "SELECT id, email, first_name, last_name, department_id FROM users WHERE email = %s;",
                (email,),
            )

            user = cursor.fetchone()
            return user

    async def search_ach_credits(self, **kwargs):
        query = ""
        params = []

        if kwargs["outstanding"]:
            query += "SELECT * FROM ach_credits WHERE claimed IS NULL "
        else:
            query += "SELECT * FROM ach_credits WHERE claimed IS NOT NULL "

        if kwargs["amount_lb"] and kwargs["amount_ub"]:
            query += "AND amount BETWEEN %s AND %s "
            params.append(kwargs["amount_lb"])
            params.append(kwargs["amount_ub"])
        elif kwargs["amount_lb"]:
            query += "AND amount > %s "
            params.append(kwargs["amount_lb"])
        elif kwargs["amount_ub"]:
            query += "AND amount < %s "

        if kwargs["fund"]:
            query += "AND fund = %s "
            params.append(kwargs["fund"])

        if kwargs["description"]:
            query += "AND description ILIKE %s "
            params.append(kwargs["description"])

        if kwargs["received_lb"] and kwargs["received_ub"]:
            query += "AND received BETWEEN %s AND %s "
            params.append(kwargs["received_lb"])
            params.append(kwargs["received_ub"])
        elif kwargs["received_lb"]:
            query += "AND received > %s "
            params.append(kwargs["received_lb"])
        elif kwargs["received_ub"]:
            query += "AND received < %s "
            params.append(kwargs["received_ub"])

        if kwargs["claimed_lb"] and kwargs["claimed_ub"]:
            query += "AND claimed BETWEEN %s AND %s "
            params.append(kwargs["claimed_lb"])
            params.append(kwargs["claimed_ub"])
        elif kwargs["claimed_lb"]:
            query += "AND claimed > %s "
            params.append(kwargs["claimed_lb"])
        elif kwargs["claimed_ub"]:
            query += "AND claimed < %s "
            params.append(kwargs["claimed_ub"])

        if kwargs["roc_id"]:
            query += "AND roc_id = %s "
            params.append(kwargs["roc_id"])

        if kwargs["department_id"]:
            query += "AND department_id = %s "
            params.append(kwargs["department_id"])

        if kwargs["skip"]:
            query += "SKIP %s "
            params.append(kwargs["skip"])

        query += "LIMIT %s"
        params.append(kwargs["limit"])

        with self.cursor() as cursor:
            cursor.execute(query, (*params,))

            ach_credits = cursor.fetchall()
            return ach_credits

    async def get_credit_descriptions(self):
        with self.cursor() as cursor:
            cursor.execute(
                """SELECT * FROM credit_descriptions cd JOIN departments d ON cd.department_id = d.id;"""
            )

            descriptions = cursor.fetchall()
            return descriptions

    async def post_description(self, credit_description: Dict):

        keywords: str = credit_description["description"].split(",")
        for keyword in keywords:
            keyword.strip()
        keywords_array = json.dumps(keywords)

        credit_description["keywords_array"] = keywords_array
        
        with self.cursor as cursor:
            cursor.execute("""
                          INSERT INTO credit_descriptions
                          (keywords_array, fund, department_id) 
                           """, credit_description.values())
    
    async def post_ach_credit(self, credit: NewAchCredit):
        with self.cursor() as cursor:
            cursor.execute("""INSERT INTO ach_credits
                            (amount_in_cents, fund, description, received, claimed, roc_id, department_id) 
                            VALUES
                            (%s, %s, %s, %s, %s, %s, %s)
                           """, credit.model_dump().values())
    
    async def bulk_import_from_csv(self, file: UploadFile):
        descriptions = self.get_credit_descriptions()
        # pdb.set_trace()
        bytes_file = file.file.read()
        file_string = bytes_file.decode("utf-8")
        string_file = io.StringIO(file_string)
        credits = csv.DictReader(string_file, delimiter=',') 

        for credit in credits:
            department_id = categorize_credit(credit, descriptions)

            credit_dict = {}
            credit_dict["amount_in_cents"] =  math.floor(float(credit["Amount"])*100)
            date_vals = [int(number) for number in credit["AsOfDate"].split('/')]
            credit_dict["received"] = str(date(date_vals[2], date_vals[0], date_vals[1]))
            credit_dict["fund"] = int(credit["AccountName"][-5:])
            credit_dict["description"] = credit["Description"]
            credit_dict["department_id"] = department_id
            new_credit: NewAchCredit = NewAchCredit(**credit_dict)
            self.post_ach_credit(new_credit)            
            


API = API(db)