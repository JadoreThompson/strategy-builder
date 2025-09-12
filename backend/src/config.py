import logging
import os
import sys
from datetime import timedelta
from multiprocessing.queues import Queue
from urllib.parse import quote

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine


PRODUCTION = False


# Paths
BASE_PATH = os.path.dirname(__file__)
RESOURCES_PATH = os.path.join(BASE_PATH, "resources")


load_dotenv(os.path.join(BASE_PATH, ".env"))


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
DB_ENGINE_SYNC = create_engine(
    f"postgresql+psycopg2://{DB_USER_CREDS}@{DB_HOST_CREDS}/{DB_NAME}"
)


# Kafka
KAFKA_POSITIONS_TOPIC = os.getenv("KAFKA_POSITIONS_TOPIC", "positions")  # Position updates from strategies
KAFKA_HOST = os.getenv("KAFKA_HOST", 'localhost')
KAFKA_PORT = int(os.getenv("KAFKA_PORT", "9092"))


# Logging
logging.basicConfig(
    filename="app.log",
    format="%(asctime)s - [%(levelname)s] - %(module)s - %(message)s",
)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    logging.Formatter("%(asctime)s - [%(levelname)s] - %(module)s - %(message)s")
)
logger.addHandler(handler)


# Resources
fpath = os.path.join(RESOURCES_PATH, "system-prompt.txt")
if not os.path.exists(fpath):
    SYSTEM_PROMPT = None
    logger.warning(f"System prompt not found at {fpath}")
else:
    SYSTEM_PROMPT = open(fpath, "r").read()


DEPLOYMENT_QUEUE: Queue = None # Must be initialised one time by __main__.py