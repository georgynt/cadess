import logging, sys, os
from logging import *
from os.path import join

logger = getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.addHandler(logging.FileHandler(join(os.getcwd(), 'cades.log')))
