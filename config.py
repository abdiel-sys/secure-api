import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "respaldototalmentesecreto")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
