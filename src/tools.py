import sys
from os.path import dirname
from logger import logger


def get_installation_dir():
    def fallback():
        if getattr(sys, 'frozen', False):
            return dirname(sys.executable)
        else:
            return dirname(__file__)

    try:  # Надо при инсталляции задать обязательно эту штуку в реестре
        if sys.platform == 'win32':
            import winreg as wr

            REG_PATH = r'SOFTWARE\CasCAdES'
            INST_DIR = 'Installation'

            try:
                regkey = wr.OpenKey(wr.HKEY_LOCAL_MACHINE, REG_PATH)
                (val, typ) = wr.QueryValueEx(regkey, INST_DIR)

                return val
            except FileNotFoundError:
                pass
    except Exception as ex:
        logger.error(ex)
    return fallback()
