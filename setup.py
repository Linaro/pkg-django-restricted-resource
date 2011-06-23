#!/usr/bin/env python
# Copyright (C) 2010 Linaro Limited
#
# Author: Zygmunt Krynicki <zygmunt.krynicki@linaro.org>
#
# This file is part of django-restricted-resource.
#
# django-restricted-resource is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# as published by the Free Software Foundation
#
# django-restricted-resource is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with django-restricted-resource.  If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup


setup(
    name='django-restricted-resource',
    version=":versiontools:django_restricted_resource:__version__",
    author="Zygmunt Krynicki",
    author_email="zygmunt.krynicki@linaro.org",
    description="Base model for Django that adds simple and efficient ownership and access control.",
    url='https://launchpad.net/django-restricted-resource',
    test_suite='django_restricted_resource.test_project.tests.run_tests',
    license='LGPLv3',
    keywords=['django', 'ownership', 'models'],
    classifiers=[
        "Development Status :: 4 - Beta",
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
    ],
    zip_safe=True,
    packages=['django_restricted_resource'],
    # dependencies
    install_requires=['django >= 1.0'],
    tests_require=['django-testscenarios >= 0.7.1'],
    setup_requires=['versiontools >= 1.3.1'],
)
