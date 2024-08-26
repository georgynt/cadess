import logging
import sys
from logging import *


logger = getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

stm_h = logging.StreamHandler(sys.stdout)
stm_h.setFormatter(formatter)

logger.addHandler(stm_h)
