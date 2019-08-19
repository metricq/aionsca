``aionsca``
===========

Asynchronously send NSCA host and service reports, as used by Nagios/Centreon.

Usage
=====

This package provides an ``async`` interface for sending NSCA reports via its
``aionsca.Client`` class:

.. code-block:: python

    from aionsca import Client, State

    async def hal3000_warn_ae35():
        async with Client(host='localhost') as client:
            await client.send_report(
                host='hal3000',
                service="AE35",
                state=State.WARNING,
                message=(
                    "I've just picked up a fault in the AE35 unit.\n"
                    "It's going to go 100% failure in 72 hours",
                )
            )

License
-------

::

  aionsca
  Copyright (C) 2019  Technische Universität Dresden

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.
