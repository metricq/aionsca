# aionsca
# Copyright (C) 2019 ZIH, Technische Universitaet Dresden, Federal Republic of Germany
#
# All rights reserved.
#
# This file is part of metricq.
#
# metricq is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# metricq is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with metricq.  If not, see <http://www.gnu.org/licenses/>.

from abc import abstractmethod
from enum import IntEnum
from typing import Callable
import os

import Crypto.Cipher.Blowfish


class Method(IntEnum):
    PLAINTEXT = 0
    BLOWFISH = 8

    def __str__(self):
        return f"{self.name.lower()} ({self.value})"


_crypters = dict()


class _MetaCrypter(type):
    def __new__(clsarg, *args, **kwargs):
        cls = super().__new__(clsarg, *args, **kwargs)
        if cls.method is not None:
            _crypters[cls.method] = cls

        return cls


class Crypter(metaclass=_MetaCrypter):
    method = None

    def __init__(self, password, iv, rng):
        self.password = password
        self.iv = iv
        self.rng = rng

    @abstractmethod
    def encrypt(self, _message: bytes) -> bytes:
        raise NotImplementedError(
            f"encrypt() not implemented for crypter {self.method!s}"
        )


class PlaintextCrypter(Crypter):
    method = Method.PLAINTEXT

    def encrypt(self, message) -> bytes:
        return bytes(message)


class Pep272Crypter(Crypter):
    """Base class for implementing crypters supporting the PEP 272 interface
    """

    CypherCls = None
    key_size = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def truncate_or_extend(
            obj: bytes, max_len: int, extend_by: Callable[[int], bytes]
        ):
            if len(obj) >= max_len:
                return obj[:max_len]
            else:
                return obj + extend_by(max_len - len(obj))

        key = truncate_or_extend(
            self.password, self.key_size, lambda diff: b"\0" * diff
        )
        iv = truncate_or_extend(self.iv, self.CypherCls.block_size, self.rng)

        self.crypter = self.CypherCls.new(key, self.CypherCls.MODE_CFB, iv)

    def encrypt(self, message):
        return self.crypter.encrypt(message)


class BlowfishCrypter(Pep272Crypter):
    method = Method.BLOWFISH
    CypherCls = Crypto.Cipher.Blowfish
    key_size = 56


def get_crypter_by_method(method: Method, iv: bytes, password: bytes, rng=os.urandom):
    try:
        CrypterCls = _crypters[Method(method)]
        return CrypterCls(password, iv, rng)
    except KeyError as e:
        raise ValueError(f"Unknown encryption method {method!s}") from e
