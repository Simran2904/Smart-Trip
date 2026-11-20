import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_mysql_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", 3306)),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE", "smarttrip_db")
        )

        if connection.is_connected():
            return connection

    except mysql.connector.Error as error:
        print("MySQL Connection Error:", error)
        raise
