from asyncio import StreamReader, StreamWriter, Queue, IncompleteReadError, start_server
from datetime import datetime
from logging import getLogger
from itertools import count
from os import getrandom

from .protocol import InitPacket, ReportPacket, PacketDecodeError
from .crypto import get_crypter_by_method, Method

logger = getLogger(__name__)


class Server:
    def __init__(
        self,
        host=None,
        port=5667,
        password="",
        encryption_method: Method = Method.PLAINTEXT,
        loop=None,
    ):
        self.host = host
        self.port = port
        self.loop = loop
        self.password = str(password).encode("utf-8")
        self.encryption_method = Method.parse(encryption_method)

        self._server = None
        self._received_reports = Queue()

    async def start_server(self):
        if self._server is None:
            self._server = await start_server(
                self._on_client_connected,
                host=self.host,
                port=self.port,
                loop=self.loop,
            )

    async def __aenter__(self):
        await self.start_server()
        return self

    async def __aexit__(self, *_ex):
        self._server.close()
        await self._server.wait_closed()
        self._server = None

    async def reports(self):
        while True:
            report = await self._received_reports.get()
            self._received_reports.task_done()
            yield report

    async def _on_client_connected(self, reader: StreamReader, writer: StreamWriter):
        timestamp = int(datetime.now().timestamp())
        iv = getrandom(128)

        crypter = get_crypter_by_method(
            method=self.encryption_method, iv=iv, password=self.password, rng=getrandom
        )

        init_packet = InitPacket.pack(iv, timestamp)
        writer.write(init_packet)
        await writer.drain()

        for packet_num in count(1):
            try:
                report_packet = crypter.decrypt(
                    await reader.readexactly(ReportPacket.SIZE)
                )
                logger.debug(
                    f"Received report #{packet_num} for on socket {writer.get_extra_info('socket', '???')}"
                )
                report = ReportPacket.unpack(report_packet)
                self._received_reports.put_nowait(report)
            except IncompleteReadError as e:
                if len(e.partial) != 0:
                    logger.warning(f"IncompleteReadError for packet #{packet_num}: {e}")
                break
            except PacketDecodeError:
                logger.exception(f"Failed to decode packet ({report_packet!r})")
                break
