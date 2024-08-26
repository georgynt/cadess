import logging, sys
from logging import *

logger = getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.addHandler(logging.FileHandler(r"C:\cades.log"))
