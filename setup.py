# Copyright (c) 2015 Jonathan Kamens.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='event_scheduler',
    version='0.0.1',
    author='Jonathan Kamens',
    author_email='jik@kamens.us',
    description=('Match event attendees with topics and time slots based on '
                 'preferences.'),
    license='GPLv3+',
    url='https://github.com/jikamens/event_scheduler',
    packages=['event_scheduler'],
    long_description=read('README.txt'),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later '
        '(GPLv3+)',
        'Programming Language :: Python',
        'Topic :: Office/Business :: Scheduling',
    ]
)
