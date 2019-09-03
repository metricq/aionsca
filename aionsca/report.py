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

import struct
import binascii
import random
import string
from logging import getLogger

from .state import State

__all__ = ["encode"]

logger = getLogger(__name__)


BYTES_LOWERCASE = bytes(ord(a) for a in string.ascii_lowercase)


def random_chars(length: int) -> bytes:
    return bytes(random.choices(BYTES_LOWERCASE, k=length))


def pad_random(s: str, max_length: int) -> bytes:
    to_pad = s.encode("utf-8")[:max_length]
    len_diff = max_length - len(to_pad)
    assert len_diff >= 0
    if len_diff > 0:
        to_pad += b"\0" + random_chars(len_diff - 1)

    assert len(to_pad) == max_length
    return to_pad


# Packet format:
# Packet {
#   version: u16,
#   _pad: [u8; 2],
#   crc: u32,
#   timestamp: u32,
#   state: u16,
#   hostname: [u8; MAX_HOSTNAME_LENGTH],
#   service: [u8; MAX_SERVICE_LENGTH],
#   message: [u8; MAX_MESSAGE_LENGTH],
#   _pad: [u8; 2],
# }

MAX_LENGTH_HOSTNAME = 64
MAX_LENGTH_SERVICE = 128
MAX_LENGTH_MESSAGE = 512


PACKET_VERSION = 3
PACKET_FORMAT = (
    f"!hxxLLh{MAX_LENGTH_HOSTNAME}s{MAX_LENGTH_SERVICE}s{MAX_LENGTH_MESSAGE}sxx"
)


def encode(
    hostname: str, service: str, state: State, message: str, timestamp: int
) -> bytes:
    hostname = pad_random(hostname, MAX_LENGTH_HOSTNAME)
    service = pad_random(service, MAX_LENGTH_SERVICE)
    message = pad_random(message, MAX_LENGTH_MESSAGE)
    crc = 0
    packet = bytearray(
        struct.pack(
            PACKET_FORMAT,
            PACKET_VERSION,
            crc,
            timestamp,
            State(state).value,
            hostname,
            service,
            message,
        )
    )
    crc = binascii.crc32(packet) & 0xFFFFFFFF
    struct.pack_into("!L", packet, 4, crc)
    return bytes(packet)
