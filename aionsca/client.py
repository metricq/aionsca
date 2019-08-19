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

import asyncio
from asyncio import StreamReader, StreamWriter
import logging
import struct
from typing import Optional

from .state import State
from .crypto import Method, Crypter, get_crypter_by_method
from . import report

logger = logging.getLogger(__name__)


class Client:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5667,
        encryption_method: Method = Method.PLAINTEXT,
        password: str = "",
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        """A client for sending NSCA reports

        :param host: str
            Address of NSCA host to send reports to
        :param host: int
            Port of NSCA host
        :param encryption_method: Method
            Method used for encrypting report, see :py:class`Method`
        :param password: str
            Password used to encrypt reports
        :param loop: Optional[asyncio.AbstractEventLoop]
            Event loop to open connection in
        """
        self._host = host
        self._port = port
        self._encryption_method = Method(encryption_method)
        self._password: bytes = str(password).encode("utf-8")
        self._loop = loop

        if self._encryption_method is not Method.PLAINTEXT and not self._password:
            logger.warning(
                f"Creating NSCA client using non-plaintext encryption method {self._encryption_method!s}, "
                f"but with empty password.\n"
                f"Is this intentional?"
            )

        logger.debug(
            f"Created NSCA client: "
            f"host={self._host}:{self._port}, "
            f"encryption_method={self._encryption_method!r}"
        )

        self._reader: Optional[StreamReader] = None
        self._writer: Optional[StreamWriter] = None
        self._iv: Optional[bytes] = None
        self._timestamp: Optional[int] = None
        self._crypter: Optional[Crypter] = None

    async def _receive_init_packet(self):
        fmt = "!128sL"
        packet = await self._reader.readexactly(struct.calcsize(fmt))
        self._iv, self._timestamp = struct.unpack(fmt, packet)
        logger.debug(f"Received init packet: timestamp: {self._timestamp}")

    async def connect(self):
        logger.debug(f"Connecting to {self._host}:{self._port}...")
        self._reader, self._writer = await asyncio.open_connection(
            host=self._host, port=self._port, loop=self._loop
        )
        await self._receive_init_packet()
        self._crypter = get_crypter_by_method(
            self._encryption_method, iv=self._iv, password=self._password
        )

    async def disconnect(self, flush=False):
        logger.debug(f"Disconnecting...")
        if self._writer is None:
            return

        try:
            if flush:
                logger.debug(f"Draining send buffer...")
                await self._writer.drain()
        except ConnectionError:
            pass
        finally:
            self._writer.close()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *_ex):
        await self.disconnect(flush=True)

    async def send_report(
        self,
        host: str,
        service: Optional[str],
        state: State,
        message: str,
        retries: int = 5,
    ):
        """Asynchronously send a state report for the service ``service`` on
        host ``host`` to the connected NSCA host.

        The parameter ``state`` must be convertible to an instance of
        :py:class`State`.

        :param host: str
            host name as configured with Nagios/Centreon
        :param service: Optional[str]
            service name as configured with Nagios/Centreon, or ``None``
        :param state: State
            State to report (``OK=0``, ``WARNING=1``, etc.), see :py:class`State`
        :param message: str
            An informational message to attach to this report
        :param retries: int
            Number of tries to send attempted before raising a
            :py:class`ConnectionError`
        """

        # A report with an empty service name is interpreted as a host report.
        service = "" if service is None else service

        state = State(state)

        logger.debug(
            f"Sending report: "
            f"host={host!r}, "
            f"service={service!r}, "
            f"state={state!r}, "
            f"message={message!r}"
        )

        for retry in range(1, retries + 1):
            try:
                report_bytes = report.encode(
                    hostname=host,
                    service=service,
                    state=state,
                    message=message,
                    timestamp=self._timestamp,
                )
                encrypted = self._crypter.encrypt(report_bytes)
                self._writer.write(encrypted)
                await self._writer.drain()
            except ConnectionResetError as e:
                logger.warning(
                    f"Connection reset by NSCA host, reconnecting ({retry}/{retries}): "
                    f"{e}"
                )
                try:
                    await self.disconnect(flush=False)
                    await self.connect()
                except ConnectionError as e:
                    logger.warning(
                        f"Failed to reconnect to NSCA host ({retry}/{retries}): {e}"
                    )
            else:
                # no exceptions raised, report was sent successfully
                break
        else:
            # retries exhausted
            raise ConnectionError(
                f"Failed to send report to NSCA host {self._host}:{self._port} "
                f"after {retry} {'try' if retry == 1  else 'tries'}"
            )
