import logging
import sys


logging.basicConfig(format="%(asctime)s - [%(levelname)s] - %(module)s - %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    logging.Formatter("%(asctime)s - [%(levelname)s] - %(module)s - %(message)s")
)
logger.addHandler(handler)
