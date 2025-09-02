import logging
import os
import sys
from datetime import timedelta
from urllib.parse import quote

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine


load_dotenv()

PRODUCTION = False


# Auth
COOKIE_ALIAS = "strat-builder-cookie"
JWT_ALGO = "HS256"
JWT_SECRET = os.getenv("COOKIE_SECRET", "secret")
JWT_EXPIRY = timedelta(days=1000)


# DB
DB_HOST_CREDS = f"{os.getenv("DB_HOST", "localhost")}:{os.getenv("DB_PORT", 5432)}"
DB_USER_CREDS = f"{os.getenv("DB_USER", "postgres")}:{quote(os.getenv("DB_PASSWORD"))}"
DB_NAME = os.getenv("DB_NAME")
DB_ENGINE = create_async_engine(
    f"postgresql+asyncpg://{DB_USER_CREDS}@{DB_HOST_CREDS}/{DB_NAME}"
)


# Logging
logging.basicConfig(format="%(asctime)s - [%(levelname)s] - %(module)s - %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    logging.Formatter("%(asctime)s - [%(levelname)s] - %(module)s - %(message)s")
)
logger.addHandler(handler)
