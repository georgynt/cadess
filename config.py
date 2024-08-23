from time import sleep

import yaml, sys, os
from watchdog.observers import Observer
from watchdog.events import FileModifiedEvent, FileSystemEvent, FileSystemEventHandler

from singleton import Singleton


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
        'fake-logic': True
    }
}


class Config(FileSystemEventHandler, metaclass=Singleton):
    CONFIG_FILE = 'cades.yaml'
    def __init__(self):
        if not os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, 'w') as f:
                yaml.dump(default_config_object, f)
            self._data = default_config_object
        else:
            self.refresh()
        super().__init__()
        self.observer = Observer()
        self.observer.schedule(self, self.CONFIG_FILE)
        self.observer.start()

    def on_modified(self, event: FileSystemEvent) -> None:
        if isinstance(event, FileModifiedEvent):
            self.refresh()

    def refresh(self):
        with open(self.CONFIG_FILE, 'r') as f:
            self._data = yaml.load(f, yaml.SafeLoader)

    @property
    def whitelist(self) -> list[str]:
        return self._data['whitelist'] or []

    @property
    def users(self) -> dict[str, str]:
        return self._data['users'] or {}

    @property
    def settings(self) -> dict:
        return self._data['settings'] or {}

    @property
    def auth_disabled(self) -> bool:
        return self.settings.get('auth') == 'disabled'

    @property
    def fake_logic(self) -> bool:
        return self.settings.get('fake-logic', False)

    @property
    def pincode(self) -> str:
        return self.settings.get('pincode', '')

if __name__ == '__main__':
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt as e:
        pass
