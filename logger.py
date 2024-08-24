import logging, sys
from logging import *

logger = getLogger()
logger.setLevel(logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
