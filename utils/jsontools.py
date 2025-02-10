"""
Unifier - A sophisticated Discord bot uniting servers and platforms
Copyright (C) 2023-present  UnifierHQ

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

import json

try:
    # noinspection PyUnresolvedReferences
    import orjson as json  # pylint: disable=import-error
    orjson_imported = True
except ImportError:
    orjson_imported = False

def dumps(*args, **kwargs) -> str:
    """Quick method to dump JSON data using orjson if available used for optimizing aiohttp performance.
    If orjson is not available, it will default to using the built-in json module."""
    result = json.dumps(*args, **kwargs)
    if not type(result) is str:
        result = result.decode()

    return result

def dumps_bytes(*args, **kwargs) -> bytes:
    """Like dumps, but returns bytes instead. Used for data backups."""
    result = json.dumps(*args, **kwargs)
    if type(result) is str:
        result = result.encode()

    return result

def loads_bytes(data, *args, **kwargs):
    """Loads bytes into a Python dictionary."""
    if orjson_imported:
        result = json.loads(data, *args, **kwargs)
    else:
        data = data.decode('utf-8')
        result = json.dumps(data, *args, **kwargs)

    return result
