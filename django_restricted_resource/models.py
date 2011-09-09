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
Unit tests for django-restricted-resources
"""

from django.core.exceptions import ValidationError
from django.contrib.auth.models import (AnonymousUser, User, Group)
from django.db import models

from django_restricted_resource.utils import filter_bogus_users
from django_restricted_resource.managers import RestrictedResourceManager


class RestrictedResource(models.Model):
    """
    Model for handling resource ownership and access rights.

    This is not a generic permission framework. Instead it's a rigid and
    simple but arguably useful model with the following properties:
        * resources are owned by exactly one user or exactly one group
        * resources are accessible to anyone if marked as public
        * resources are accessible to owner if owned by user
        * resources are accessible to members if owned by group
        * What the access actually permits is not defined

    This similar to the UNIX permission system with the following
    differences:
        * There are no separate READ, WRITE, EXECUTE nor STICKY bits per
          any of the possible user classes (OWNER, GROUP MEMBER, OTHER).
          Instead the application is free to use any desired policy to
          define actions a particular user may invoke on a resource that
          he can already access.
        * There is a dedicated "public" flag indicating that anyone can
          access the specified resource.
        * (important) Enumeration of resources that user can access is
          very efficient when implemented in a relational database.
    """
    NO_ACCESS, PUBLIC_ACCESS, PRIVATE_ACCESS, SHARED_ACCESS = range(4)

    user = models.ForeignKey(User, null=True, blank=True)
    group = models.ForeignKey(Group, null=True, blank=True)
    is_public = models.BooleanField()

    objects = RestrictedResourceManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
        Validate and save the resource
        """
        self.clean()
        return super(RestrictedResource, self).save(*args, **kwargs)

    def clean(self):
        """
        Make sure that ownership constraint is met.

        RestrictedResource must be owned by exactly one user or exactly
        one group.
        """
        if self.user is not None and self.group is not None:
            raise ValidationError(
                'Cannot be owned by user and group at the same time')
        if self.user is None and self.group is None:
            raise ValidationError(
                'Must be owned by someone')
        if hasattr(models.Model, "clean"):
            return super(RestrictedResource, self).clean()

    def _set_owner(self, owner):
        if not isinstance(owner, (User, Group)):
            raise TypeError("Expected User or Group instance as argument")
        if isinstance(owner, User):
            self.user = owner
            self.group = None
        else:
            self.group = owner
            self.user = None

    def _get_owner(self):
        return self.user or self.group

    owner = property(
        _get_owner, _set_owner, None,
        "Principal owner (either User or Group) of this restricted resource")

    def is_accessible_by(self, principal):
        """
        Check if the resource can be accessed by the specified principal.
        """
        return self.get_access_type(principal) != self.NO_ACCESS

    def is_owned_by(self, principal):
        """
        Check if the resource is owned by the specified principal.

        The principal may be any user or group
        """
        if principal is None:
            return False
        # If the principal is an User then this object is owned by that user or
        # the group the user belongs to.
        if isinstance(principal, (User, AnonymousUser, type(None))):
            user = filter_bogus_users(principal)
            if user is None:
                return False
            if self.user is not None:
                return self.user == user
            else:
                return self.group in user.groups.all()
        # If the principal is a Group then this object is owned by that group
        elif isinstance(principal, Group):
            group = principal
            return self.group == group
        else:
            raise TypeError("Expected User or Group instance as argument")

    def get_access_type(self, principal):
        """
        Determine the mode of access the principal has to this object:

        Possible access types:
            NO_ACCESS
                No access to restricted resource
            PUBLIC_ACCESS
                Granted to:
                    * User (including owner) accessing publicly
                      available resource
                    * Groups accessing publicly available resource
                    * None (including Anonymous users and blocked users)
                      accessing publicly available resources
            PRIVATE_ACCESS
                Granted to:
                    * Owner accessing otherwise private resource
            SHARED_ACCESS
                Granted to:
                    * User accessing restricted data via membership
                    * Groups accessing restricted data they own
        """
        if isinstance(principal, (User, AnonymousUser, type(None))):
            user = filter_bogus_users(principal)
            return self._get_access_type_for_user(user)
        elif isinstance(principal, Group):
            group = principal
            return self._get_access_type_for_group(group)
        else:
            raise TypeError("Expected User or Group instance as argument")

    def _get_access_type_for_user(self, user):
        # Allow anyone to access public data
        if self.is_public:
            return self.PUBLIC_ACCESS
        # Allow access for owners
        if self.user is not None and self.user == user:
            return self.PRIVATE_ACCESS
        # Allow access for team members
        if self.group is not None and user is not None:
            if self.group in user.groups.all():
                return self.SHARED_ACCESS
        # Finally, disallow
        return self.NO_ACCESS

    def _get_access_type_for_group(self, group):
        # Allow anyone to access public data
        if self.is_public:
            return self.PUBLIC_ACCESS
        # Allow access to group if group is the owner
        if self.group is not None and self.group == group:
            return self.SHARED_ACCESS
        # Finally, disallow
        return self.NO_ACCESS
