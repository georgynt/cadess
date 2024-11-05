#from asyncio import Lock
from os.path import join
from urllib.parse import urlsplit

from time import sleep

import yaml, sys, os
from watchdog.observers import Observer
from watchdog.events import FileModifiedEvent, FileSystemEvent, FileSystemEventHandler

from logger import logger
from singleton import Singleton
from tools import get_installation_dir


def workon_win() -> bool:
    return sys.platform == 'win32'


default_config_object = {
    'users': {
        'admin': 'admin123'
    },
    'whitelist': [
        '127.0.0.1'
    ],
    'settings': {
        'certnumber': '',
        'pincode': '',
        'fake-logic': True,
        'certificate-store': 4
    },
    "diadoc": {
        "client-id": None,
        "url": None,
        "login": None,
        "password": None
    },
    "callbacks": None,
    "db-connection-string": f"sqlite+aiosqlite:///{join(get_installation_dir(), 'cades.db')}"
}


class Config(FileSystemEventHandler, metaclass=Singleton):
    CONFIG_FILE = 'cades.yaml'
    _data: dict[str, dict[str, str|int|bool]|list[str]]

    def __init__(self):
#        self._lock = Lock()
        if not os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, 'w') as f:
                yaml.dump(default_config_object, f)
            self._data = default_config_object
        else:
            self.refresh()
        super().__init__()
        self.observer = Observer()
        if workon_win():
            self.observer.schedule(self, '.', True)
        else:
            self.observer.schedule(self, self.CONFIG_FILE, False)
        self.observer.start()

    if workon_win():
        def on_modified(self, event: FileSystemEvent) -> None:
            if (isinstance(event, FileModifiedEvent)
                        and not event.is_directory)\
                        and event.src_path.endswith(self.CONFIG_FILE):
                self.refresh()
    else:
        def on_modified(self, event: FileSystemEvent):
            if isinstance(event, FileModifiedEvent):
                self.refresh()

    def save(self):
        # async with self._lock:
        if self._data:
            with open(self.CONFIG_FILE, 'w') as f:
                yaml.dump(self._data, f)

    def refresh(self):
        with open(self.CONFIG_FILE, 'r') as f:
            if data := yaml.load(f, yaml.SafeLoader):
                self._data = data
            logger.debug(self._data)

    @property
    def whitelist(self) -> list[str]:
        return self._data['whitelist'] or []

    @property
    def users(self) -> dict[str, str]:
        return self._data['users'] or {}

    @property
    def settings(self) -> dict:
        return self._data.get('settings') or {}

    @property
    def auth_disabled(self) -> bool:
        return self.settings.get('auth') == 'disabled'

    @property
    def fake_logic(self) -> bool:
        return self.settings.get('fake-logic', False)

    @property
    def pincode(self) -> str:
        return str(self.settings.get('pincode', ''))

    @property
    def client_id(self) -> str:
        return self._data.get('diadoc', {}).get('client-id',"")

    @client_id.setter
    def client_id(self, value: str):
        # with self._lock:
        self._data['diadoc']['client-id'] = value
        self.save()

    @property
    def diadoc_url(self) -> str:
        return self._data.get("diadoc",{}).get('url', "")

    @diadoc_url.setter
    def diadoc_url(self, value: str):
        # with self._lock:
        self._data['diadoc']['url'] = value
        self.save()

    @property
    def diadoc_login(self) -> str:
        return self._data['diadoc']['login']

    @diadoc_login.setter
    def diadoc_login(self, value: str):
        # with self._lock:
        self._data['diadoc']['login'] = value
        self.save()

    @property
    def diadoc_password(self) -> str:
        return self._data['diadoc']['password']

    @diadoc_password.setter
    def diadoc_password(self, value: str):
        self._data['diadoc']['password'] = value
        self.save()

    @property
    def capicom_store(self) -> int:
        return self._data.get('settings', {}).get('certificate-store', 1)

    @property
    def test_sign(self) -> bool:
        return self._data.get('settings', {}).get('test-sign', False)

    @property
    def callback_urls(self) -> list[str]:
        return self._data.get('callbacks', []) or []

    @property
    def dbscheme(self) -> str:
        sr = urlsplit(self.dbcnxstr)
        return sr.scheme

    @property
    def dbcnxstr(self) -> str:
        return self._data.get('db-connection-string', f"sqlite+aiosqlite:///{join(get_installation_dir(), 'cades.db')}")

    @property
    def certnumber(self) -> str:
        return self.settings.get("certnumber", None)

if __name__ == '__main__':
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt as e:
        pass
