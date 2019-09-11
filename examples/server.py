#!/usr/bin/env python3

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
import logging
from functools import wraps
from textwrap import indent
from datetime import datetime

import click
import click_log


from aionsca.server import Server


def comain(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


class LogFormatter(logging.Formatter):
    colors = {
        "error": dict(fg="red"),
        "exception": dict(fg="red"),
        "critical": dict(fg="red"),
        "debug": dict(fg="blue"),
        "warning": dict(fg="yellow"),
    }

    def format(self, record: logging.LogRecord):
        if not record.exc_info:
            level = record.levelname.lower()
            msg = record.getMessage()
            if level in self.colors:
                prefix = click.style(f"{level}:{record.name}: ", **self.colors[level])
                msg = "\n".join(prefix + x for x in msg.splitlines())
            return msg
        return logging.Formatter.format(self, record)


logger = logging.getLogger()
handler = click_log.ClickHandler()
handler.formatter = LogFormatter()
logger.addHandler(handler)


@click.command()
@click.option("--encryption-method", "-e", default="plaintext")
@click.option("--password", "-p", default="", envvar="NSCA_HOST_PASSWORD")
@click_log.simple_verbosity_option(logger)
@comain
async def run(encryption_method, password):
    async with Server(
        "localhost", 5667, encryption_method=encryption_method, password=password
    ) as server:
        async for report in server.reports():
            host, service, state, message, timestamp = report
            logger.info(
                f"Received report:\n"
                f"  host: {host}\n"
                f"  service: {service}\n"
                f"  state: {state.name}\n"
                f"  time: {datetime.fromtimestamp(timestamp).isoformat()}\n"
                f"  message:\n"
                f"{indent(message, '    ')}\n"
            )


if __name__ == "__main__":
    asyncio.run(run())
