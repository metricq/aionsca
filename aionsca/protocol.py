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

from .state import State

BYTES_LOWERCASE = bytes(ord(a) for a in string.ascii_lowercase)


def random_chars(length: int) -> bytes:
    return bytes(random.choices(BYTES_LOWERCASE, k=length))


def random_bytes_padded(s: str, max_length: int) -> bytes:
    to_pad = s.encode("utf-8")[: max_length - 1] + b"\0"
    len_diff = max_length - len(to_pad)
    assert len_diff >= 0
    if len_diff > 0:
        to_pad += random_chars(len_diff - 1)

    assert len(to_pad) == max_length
    return to_pad


def chop_padding(b: bytes) -> str:
    content: bytes = b.split(b"\0")[0]
    return content.decode("utf-8")


class InitPacket:
    _FMT = "!128sL"
    SIZE = struct.calcsize(_FMT)

    @classmethod
    def unpack(cls, packet: bytes) -> (bytes, int):
        return struct.unpack(cls._FMT, packet)

    @classmethod
    def pack(cls, iv: bytes, timestamp: int) -> bytes:
        return struct.pack(cls._FMT, iv, timestamp)


# Packet format:
# ReportPacket {
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


class ReportPacket:
    MAX_LENGTH_HOSTNAME = 64
    MAX_LENGTH_SERVICE = 128
    MAX_LENGTH_MESSAGE = 4096

    PACKET_VERSION = 3
    _FMT = f"!hxxLLh{MAX_LENGTH_HOSTNAME}s{MAX_LENGTH_SERVICE}s{MAX_LENGTH_MESSAGE}sxx"
    SIZE = struct.calcsize(_FMT)

    @classmethod
    def pack(
        cls, hostname: str, service: str, state: State, message: str, timestamp: int
    ) -> bytes:
        hostname = random_bytes_padded(hostname, cls.MAX_LENGTH_HOSTNAME)
        service = random_bytes_padded(service, cls.MAX_LENGTH_SERVICE)
        message = random_bytes_padded(message, cls.MAX_LENGTH_MESSAGE)
        crc = 0
        packet = bytearray(
            struct.pack(
                cls._FMT,
                cls.PACKET_VERSION,
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

    @classmethod
    def unpack(cls, packet: bytes) -> (str, str, State, str, int):
        version, crc, timestamp, state, hostname, service, message = struct.unpack(
            cls._FMT, packet
        )
        if version != cls.PACKET_VERSION:
            raise ReportUnexpectedVersionError(version)
        # TODO: CRC check
        if crc or False:
            pass

        return (
            chop_padding(hostname),
            chop_padding(service),
            State(state),
            chop_padding(message),
            timestamp,
        )


class PacketDecodeError(ValueError):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)


class ReportChecksumMismatchError(PacketDecodeError):
    def __init__(self, expected: int, actual: int):
        self.expected = expected
        self.actual = actual
        super().__init__(
            self,
            f"Checksum mismatch in packet: expected {expected:04x}, got {actual:04x}",
        )


class ReportUnexpectedVersionError(PacketDecodeError):
    def __init__(self, version: int):
        self.version = version
        self.bytes = struct.pack("!h", self.version)
        super().__init__(
            self, f"Unexpected version number: {version} (bytes: {self.bytes})"
        )
