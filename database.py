import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={os.getenv('SQL_SERVER')};"
        f"DATABASE={os.getenv('SQL_DATABASE')};"
        f"UID={os.getenv('SQL_USERNAME')};"
        f"PWD={os.getenv('SQL_PASSWORD')};"
    )
