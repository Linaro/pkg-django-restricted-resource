#!/usr/bin/python
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

import os
import sys

def find_sources():
    base_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..")
    if os.path.exists(os.path.join(base_path, "django_restricted_resource")):
        sys.path.insert(0, base_path)


find_sources()
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_project.settings'


from django.test.utils import get_runner
from django.conf import settings


def run_tests():
    runner = get_runner(settings)(verbosity=2, interactive=False)
    failures = runner.run_tests(['django_restricted_resource'])
    sys.exit(failures)


if __name__ == '__main__':
    run_tests()
