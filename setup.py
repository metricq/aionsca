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
from setuptools import setup, find_packages

with open("README.rst", "r") as readme:
    long_description = readme.read()

setup(
    name="aionsca",
    version="1.0.0",
    author="Philipp Joram",
    author_email="philipp [dot] joram [at] tu-dresden [dot] de",
    description="Asynchronously send NSCA host and service reports",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    packages=find_packages(),
    scripts=[],
    install_requires=["pycrypto~=2.0"],
    extras_require={"examples": ["click~=7.0", "click-log>=0.3.2"]},
)
