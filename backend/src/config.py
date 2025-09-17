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

logger = logging.getLogger("group_coordinator")
logger.setLevel(logging.DEBUG)


# Auth
COOKIE_ALIAS = "strat-builder-cookie"
JWT_ALGO = "HS256"
JWT_SECRET = os.getenv("COOKIE_SECRET", "secret")
JWT_EXPIRY = timedelta(days=1000)


# DB
DB_HOST_CREDS = f"{os.getenv("DB_HOST", "localhost")}:{os.getenv("DB_PORT", 5432)}"
DB_USER_CREDS = f"{os.getenv("DB_USER", "postgres")}:{quote(os.getenv("DB_PASSWORD"))}"
DB_NAME = os.getenv("DB_NAME", "strat_builder")
DB_ENGINE = create_async_engine(
    f"postgresql+asyncpg://{DB_USER_CREDS}@{DB_HOST_CREDS}/{DB_NAME}"
)
DB_ENGINE_SYNC = create_engine(
    f"postgresql+psycopg2://{DB_USER_CREDS}@{DB_HOST_CREDS}/{DB_NAME}"
)


# Kafka
KAFKA_POSITIONS_TOPIC = os.getenv(
    "KAFKA_POSITIONS_TOPIC", "positions"
)  # Position updates from log worker
KAFKA_POSITIONS_LOGGER_TOPIC = os.getenv(
    "KAFKA_POSITIONS_LOGGER_TOPIC", "positions_logger"
)  # Position updates from strategies
KAFKA_HOST = os.getenv("KAFKA_HOST", "localhost")
KAFKA_PORT = int(os.getenv("KAFKA_PORT", "9092"))


# LLM
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_AGENT_ID = os.getenv("LLM_AGENT_ID")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "devstral-small-latest")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.mistral.ai/v1")

fpath = os.path.join(RESOURCES_PATH, "system-prompt.txt")
if not os.path.exists(fpath):
    SYSTEM_PROMPT = None
    logger.warning(f"System prompt not found at {fpath}")
else:
    SYSTEM_PROMPT = open(fpath, "r").read()


class Dummy:
    def put_nowait(self, *args, **kw): ...


DEPLOYMENT_QUEUE: Queue = Dummy()  # Must be initialised by main.py
