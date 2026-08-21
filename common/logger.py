import logging
import sys

logger = logging.getLogger("autotest")
logger.setLevel(logging.INFO)

if not logger.handlers:
    _h = logging.StreamHandler(sys.stdout)
    _h.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    logger.addHandler(_h)
