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

def filter_bogus_users(user):
    """
    Check for bogus instances of user (anonymous, disabled, etc) and
    change them to None. This simplifies user comparison and handling.
    If the user is `None' then he's not trusted, period, no need to
    check deeper.
    """
    if user is not None and user.is_authenticated() and user.is_active:
        return user
