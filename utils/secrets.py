"""
Unifier - A sophisticated Discord bot uniting servers and platforms
Copyright (C) 2024  Green, ItsAsheer

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import json
import base64
import traceback
from dotenv import load_dotenv
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES
from Crypto import Random as CryptoRandom
from Crypto.Util.Padding import pad, unpad

# import ujson if installed
try:
    import ujson as json  # pylint: disable=import-error
except:
    pass

class Encryptor:
    def __init__(self):
        pass

    def encrypt(self, encoded, password, salt):
        __key = PBKDF2(password, salt, dkLen=32)

        iv = CryptoRandom.get_random_bytes(16)
        __cipher = AES.new(__key, AES.MODE_CBC, iv=iv)
        result = __cipher.encrypt(pad(encoded, AES.block_size))
        del __key
        del __cipher
        return result, base64.b64encode(iv).decode('ascii')

    def decrypt(self, encrypted, password, salt, iv_string):
        iv = base64.b64decode(iv_string)
        __key = PBKDF2(password, salt, dkLen=32)
        __cipher = AES.new(__key, AES.MODE_CBC, iv=iv)
        result = unpad(__cipher.decrypt(encrypted), AES.block_size)
        del __key
        del __cipher
        return result

class TokenStore:
    def __init__(self, encrypted, password=None, salt=None, debug=False, content_override=None):
        self.__is_encrypted = encrypted
        self.__encryptor = Encryptor()
        self.__password = password
        self.__salt = salt

        if encrypted:
            if not password:
                raise ValueError('encryption password must be provided')
            if not salt:
                raise ValueError('encryption salt must be provided')

            # file is in json format
            try:
                with open('.encryptedenv', 'r') as file:
                    self.__data = json.load(file)
                with open('.ivs', 'r') as file:
                    self.__ivs = json.load(file)
            except:
                self.__data = {}
                self.__ivs = {}
        else:
            # file is in dotenv format, load using load_dotenv
            # we will not encapsulate dotenv data for the sake of backwards compatibility
            if content_override:
                # content override is a feature only to be used by bootloader
                self.__data = content_override
            else:
                load_dotenv()
                self.__data = os.environ

        self.__debug = debug

    @property
    def encrypted(self):
        return self.__is_encrypted

    @property
    def ivs(self):
        # initialization vectors are public, so they can be safely displayed in plaintext
        return self.__ivs

    @property
    def debug(self):
        return self.__debug

    @property
    def tokens(self):
        if not self.__is_encrypted:
            raise ValueError('cannot retrieve keys when tokens are unencrypted')

        tokens = list(self.__data.keys())
        tokens.remove('test')
        return tokens

    def to_encrypted(self, password, salt):
        dotenv = open('.env', 'r')
        lines = dotenv.readlines()
        dotenv.close()

        keys = []
        for line in lines:
            key = line.split('=', 1)[0]
            while key.endswith(' '):
                key = key[:-1]
            keys.append(key)

        encrypted_env = {'test': None}
        ivs = {'test': None}

        test_value, test_iv = self.__encryptor.encrypt(str.encode(
            'This can be anything, as long as it is a string. Otherwise, except decryption test to fail.'
        ), password, salt)

        encrypted_env['test'] = base64.b64encode(test_value).decode('ascii')
        ivs['test'] = test_iv

        # we can get values from dotenv, since that's been done if TokenStore is not encrypted

        for key in keys:
            __token = os.environ.get(key)
            if not __token:
                continue

            encrypted_value, iv = self.__encryptor.encrypt(str.encode(__token), password, salt)
            encrypted_env.update({key: base64.b64encode(encrypted_value).decode('ascii')})
            ivs.update({key: iv})
            del os.environ[key]

        with open('.encryptedenv', 'w+') as file:
            # noinspection PyTypeChecker
            json.dump(encrypted_env, file)

        with open('.ivs', 'w+') as file:
            # noinspection PyTypeChecker
            json.dump(ivs, file)

        self.__data = encrypted_env
        self.__ivs = ivs
        self.__password = password
        self.__salt = salt
        self.__is_encrypted = True

    def test_decrypt(self, password=None):
        if not self.__is_encrypted:
            return True

        try:
            self.__encryptor.decrypt(base64.b64decode(self.__data['test']), password or self.__password, self.__salt, self.__ivs['test'])
        except:
            if self.__debug:
                traceback.print_exc()

            return False
        return True

    def retrieve(self, identifier):
        data = str.encode(self.__data[identifier])
        iv = self.__ivs[identifier]
        decrypted = self.__encryptor.decrypt(base64.b64decode(data), self.__password, self.__salt, iv)
        return decrypted.decode('utf-8')

    def add_token(self, identifier, token):
        if identifier in self.__data.keys():
            raise KeyError('token already exists')

        encrypted, iv = self.__encryptor.encrypt(str.encode(token), self.__password, self.__salt)
        self.__data.update({identifier: base64.b64encode(encrypted).decode('ascii')})
        self.__ivs.update({identifier: iv})
        self.save('.encryptedenv', '.ivs')
        return len(self.__data)

    def replace_token(self, identifier, token, password):
        # password prompt to prevent unauthorized token deletion
        if not self.test_decrypt(password=password):
            raise ValueError('invalid password')

        if not identifier in self.tokens:
            raise KeyError('token does not exist')

        encrypted, iv = self.__encryptor.encrypt(str.encode(token), self.__password, self.__salt)
        self.__data.update({identifier: base64.b64encode(encrypted).decode('ascii')})
        self.__ivs.update({identifier: iv})
        self.save('.encryptedenv', '.ivs')

    def delete_token(self, identifier, password):
        # password prompt to prevent unauthorized token deletion
        if not self.test_decrypt(password=password):
            raise ValueError('invalid password')

        if not identifier in self.tokens:
            raise KeyError('token does not exist')

        del self.__data[identifier]
        del self.__ivs[identifier]
        self.save('.encryptedenv', '.ivs')
        return len(self.__data)

    def reencrypt(self, current_password, password, salt):
        if not self.test_decrypt(password=current_password):
            raise ValueError('invalid password')

        for key in self.__data.keys():
            token = self.retrieve(key)
            encrypted, iv = self.__encryptor.encrypt(str.encode(token), password, salt)
            self.__data[key] = base64.b64encode(encrypted).decode('ascii')
            self.__ivs[key] = iv

        self.__password = password
        self.__salt = salt
        self.save('.encryptedenv', '.ivs')

    def save(self, filename, iv_filename):
        if not self.__is_encrypted:
            raise ValueError('cannot save unencrypted data')

        with open(filename, 'w+') as file:
            # noinspection PyTypeChecker
            json.dump(self.__data, file)

        with open(iv_filename, 'w+') as file:
            # noinspection PyTypeChecker
            json.dump(self.__ivs, file)
