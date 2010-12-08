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

"""
Module with model manager for RestrictedResource
"""

from django.contrib.auth.models import (User, AnonymousUser, Group)
from django.db.models import Q
from django.db import models

from django_restricted_resource.utils import filter_bogus_users


class RestrictedResourceManager(models.Manager):
    """
    Model manager for RestrictedResource and subclasses that has
    additional methods.

    The extra methods are:
        * owned_by_principal(principal)
        * accessible_by_principal(principal)

    Both methods allow for efficient enumeration of owned and accessible
    resources (respectively).

    There is one extra convenience method:
        * accessible_by_anyone()
    That is equivalent to accessible_by_principal(None) but is more
    expressive in intent.
    """

    def owned_by_principal(self, principal):
        """
        Return a QuestySet of RestrictedResource instances that are
        owned by the specified principal, which can be a User or Group
        instance.
        """
        if isinstance(principal, (User, AnonymousUser, type(None))):
            user = filter_bogus_users(principal)
            return self._owned_by_user(user)
        elif isinstance(principal, Group):
            group = principal
            return self._owned_by_group(group)
        else:
            raise TypeError("Expected User or Group instance as argument")

    def accessible_by_principal(self, principal):
        """
        Return a QuerySet of RestrictedResource instances that can be
        accessed by specified principal. The principal may be None,
        AnonymousUser, valid User or valid Group.

        Note: All objects that can be accessed are returned, not just
        objects with exclusive access. To determine why a particular
        principal can access a particular resource use
        RestrictedResource.get_access_type(principal).
        """
        if isinstance(principal, (User, AnonymousUser, type(None))):
            user = filter_bogus_users(principal)
            return self._accessible_by_user(user)
        elif isinstance(principal, Group):
            group = principal
            return self._accessible_by_group(group)
        else:
            raise TypeError("Expected User or Group instance as argument")

    def accessible_by_anyone(self):
        """
        Return a QuerySet of BundleStream instances that can be accessed
        by anyone.
        """
        return self._accessible_by_user(None)

    def _accessible_by_user(self, user):
        if user is None:
            return self.filter(is_public=True)
        else:
            return self.filter(
                Q(is_public = True) |
                Q(user = user) |
                Q(group__in = user.groups.all()))

    def _accessible_by_group(self, group):
        # None gets mapped to users, there is no chance to get None here
        assert group is not None
        return self.filter(
            Q(is_public = True) |
            Q(group = group))

    def _owned_by_user(self, user):
        if user is None:
            return self.none()
        else:
            return self.filter(
                Q(user = user) |
                Q(group__in = user.groups.all()))

    def _owned_by_group(self, group):
        # None gets mapped to users, there is no chance to get None here
        assert group is not None
        return self.filter(group = group)
