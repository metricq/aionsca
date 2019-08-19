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
import sys
from functools import wraps
from typing import Dict, TextIO, Optional

import click
import click_log

from aionsca import Client, EncryptionMethod


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


def parse_config_file(fp: TextIO) -> Dict[str, str]:
    config: Dict[str, str] = dict()
    line: str
    for line in fp:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            key, value = line.split("=", 1)
            config[key] = value.strip()
        except ValueError as e:
            raise ValueError(f"Invalid config key {line}") from e
    return config


@click.command()
@click_log.simple_verbosity_option(logger)
@click.argument("host", default="localhost", metavar="ADDRESS")
@click.option(
    "--port", "-p", default=5667, type=int, metavar="NUM", help="NSCA host port"
)
@click.option(
    "--delimiter",
    "-d",
    default="\t",
    type=str,
    metavar="DELIM",
    help="Delimiter to used when parsing input",
)
@click.option(
    "--config-file",
    "-c",
    default="/etc/send_nsca.cfg",
    type=click.File(mode="r"),
    help="Name of config file to use",
)
@comain
async def main(host: str, port: int, delimiter: str, config_file: Optional[click.File]):
    try:
        config = parse_config_file(config_file) if config_file else dict()

        password = config.get("password", "")
        encryption_method = config.get("encryption_method", EncryptionMethod.PLAINTEXT)
    except ValueError as e:
        logger.error(f"Failed to parse config file: {e}")
        sys.exit(1)

    logger.debug(config)

    async with Client(
        host=host, port=port, encryption_method=encryption_method, password=password
    ) as client:
        for line in sys.stdin:
            split = line.split(delimiter, maxsplit=4)
            if len(split) == 4:
                check_host, service, state, message = split
            elif len(split) == 3:
                check_host, state, message = split
                service = None
            else:
                raise ValueError(f"Invalid report")

            await client.send_report(
                host=check_host, state=int(state), message=message, service=service
            )


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
