import time
import sqlite3
import orjson
from typing import Optional, Any

class Data:
    def __init__(self):
        self.__data: dict = {}

class BridgeData(Data):
    def __init__(self, data: Optional[dict] = None):
        super().__init__()

        if data:
            self.__data = data

    def get_room(self, room_id: str) -> dict:
        return self.__data.get('rooms', {}).get(room_id)

# TODO:
# - Add message ID indexing table (message ID to CC ID - use HMAC)
# - Add HMAC secret table (use similar structure to content table)

# noinspection SqlResolve,SqlNoDataSourceInspection
class HotColdData(Data):
    """A hot and cold data cache for storing data in memory and on disk."""

    def __init__(self, encryptor: Any, db_filename: str, soft_limit: int = 1000, hard_limit: int = 1500,
                 data: Optional[dict] = None):
        super().__init__()
        self.__encryptor = encryptor
        self.__soft_limit = soft_limit
        self.__hard_limit = hard_limit

        if data:
            self.__data = data

        self.__db = sqlite3.connect(db_filename)
        self.__cursor = self.__db.cursor()

        # DB structure
        # key: str, nonce: str, tag: str, salt: str, ciphertext: str
        self.__cursor.execute(
            'CREATE TABLE IF NOT EXISTS coldcache (key INT PRIMARY KEY, nonce TEXT, tag TEXT, salt TEXT, ciphertext TEXT)'
        )
        self.__cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS key_index ON coldcache(key)')
        self.__db.commit()

        self.__cursor.execute('SELECT COUNT(*) FROM coldcache')
        self.__cold_id = self.__cursor.fetchone()[0]

        if not self.__cold_id:
            self.__cold_id = 0

    @property
    def cold_id(self) -> int:
        value = self.__cold_id
        self.__cold_id += 1
        return value

    def _add_hot(self, value: dict):
        value['accessed'] = time.time()
        value['cold_id'] = self.cold_id
        self.__data[value['cold_id']] = value

        if len(self.__data) > self.__hard_limit:
            # get keys sorted by timestamp of message
            keys = sorted(self.__data.keys(), key=lambda x: self.__data[x].get('accessed', self.__data[x].get('timestamp')))
            to_remove = len(self.__data) - self.__soft_limit

            # evict oldest messages to cold
            for key in keys[:to_remove]:
                self._add_cold(self.__data.pop(key))

    def _get_cold(self, key: str) -> Optional[dict]:
        self.__cursor.execute('SELECT * FROM coldcache WHERE key = ?', (key,))
        data = self.__cursor.fetchone()

        if data:
            nonce = data[1]
            tag = data[2]
            salt = data[3]
            ciphertext = data[4]
            decrypted = self.__encryptor.decrypt(nonce, tag, salt, ciphertext)
            decrypted_dict = orjson.loads(decrypted)
            self._add_hot(decrypted_dict)

        return None

    def _add_cold(self, value: dict):
        data = self.__encryptor.encrypt(orjson.dumps(value))
        nonce = data['nonce']
        tag = data['tag']
        salt = data['salt']
        ciphertext = data['ciphertext']
        key = value['cold_id']

        # insert to DB, override existing w/ same key if exists
        self.__cursor.execute(
            'INSERT OR REPLACE INTO coldcache VALUES (?, ?, ?, ?, ?)',
            (key, nonce, tag, salt, ciphertext)
        )
        self.__db.commit()

    def get(self, key: str) -> Optional[dict]:
        """Returns data from cache."""
        return self.__data.get(key) or self._get_cold(key)
