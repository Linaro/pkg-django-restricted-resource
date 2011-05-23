# Copyright (C) 2010 Linaro Limited
#
# Author: Zygmunt Krynicki <zygmunt.krynicki@linaro.org>
#
# This file is part of Launch Control.
#
# Launch Control is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3
# as published by the Free Software Foundation
#
# Launch Control is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Launch Control.  If not, see <http://www.gnu.org/licenses/>.

import inspect
import itertools

from django.contrib.auth.models import (AnonymousUser, User, Group)
from django.db import models
from django_testscenarios.ubertest import (TestCase, TestCaseWithScenarios)

from django_restricted_resource.models import RestrictedResource


class TestCaseWithInvariants(TestCaseWithScenarios):
    """
    TestCase that generates test scenarios based on the
    possible combination of invariants.

    Invariants are declared by the 'invariants' variable defined in
    class scope. The variable must point to a dictionary. Each element
    of that dictionary becomes a test invariant. The value of that
    dictionary may be one of:
        * list: Each of the elements is checked. If all elements are of
          simple type (int, bool, string) then parameter description
          will contain them as-is, otherwise they will be described as
          "variant-N"
        * dict: Each of the values is checked. In addition the keys will
          be used to construct meaningful parameter descriptions.
    """

    def _get_invariants(self):
        return getattr(self, 'invariants', {})

    def _get_scenarios(self):
        if hasattr(self, "scenarios"):
            return self.scenarios
        self.scenarios = self._get_all_possible_scenarios(
            self._get_invariants())
        return self.scenarios

    def _dict_to_keys_and_values(self, d):
        pairs = d.items()
        keys = [first for (first, second) in pairs]
        values = [second for (first, second) in pairs]
        return keys, values

    def _get_all_possible_scenarios(self, invariants):
        scenarios = []
        invariant_keys, invariant_values = self._dict_to_keys_and_values(invariants)
        scenario_ids_list = []
        scenario_params_list = []
        for value in invariant_values:
            if isinstance(value, list):
                if all([isinstance(variant, (int, bool, str)) for variant in value]):
                    scenario_ids_list.append([repr(variant) for variant in value])
                else:
                    scenario_ids_list.append(['variant-%d' % variant for variant in range(len(value))])
                scenario_params_list.append(value)
            elif isinstance(value, dict):
                k, v = self._dict_to_keys_and_values(value)
                scenario_ids_list.append(k)
                scenario_params_list.append(v)
        for scenario_ids, scenario_params in itertools.izip(
            itertools.product(*scenario_ids_list),
            itertools.product(*scenario_params_list)):
            parameters = dict(zip(invariant_keys, scenario_params))
            name = ", ".join([
                "%s=%s" % (invariant_key, param_id)
                for (invariant_key, param_id)
                in zip(invariant_keys, scenario_ids)])
            scenario = (name, parameters)
            scenarios.append(scenario)
        return scenarios

    def setUp(self):
        super(TestCaseWithScenarios, self).setUp()
        # Evaluate lazy invariants now that `self' is around
        for invariant in self._get_invariants().iterkeys():
            value = getattr(self, invariant)
            if inspect.isfunction(value):
                value = value(self)
                setattr(self, invariant, value)


class ExampleRestrictedResource(RestrictedResource):
    """
    Dummy model to get non-abstract model that inherits from
    RestrictedResource
    """
    name = models.CharField(max_length=100, null=True, unique=True)

    class Meta:
        ordering = ['name']


class FixtureHelper(object):

    def getUniqueString(self, prefix=None, max_length=None):
        value = super(FixtureHelper, self).getUniqueString(prefix)
        if max_length is not None:
            if len(value) >= max_length:
                value = super(FixtureHelper, self).getUniqueString("short")
                if len(value) >= max_length:
                    raise ValueError("Unable to satisfy request for random string with max_length=%d" % max_length)
        return value

    def getUniqueStringForField(self, model, field_name):
        return self.getUniqueString(max_length=model._meta.get_field_by_name(field_name)[0].max_length)

    def getUniqueUser(self, is_active=True):
        user = User.objects.create(
            username=self.getUniqueStringForField(User, "username"),
            is_active = is_active)
        self.addCleanup(user.delete)
        return user

    def getUniqueGroup(self):
        group = Group.objects.create(
            name = self.getUniqueStringForField(Group, "name"))
        self.addCleanup(group.delete)
        return group

    def getUniqueResource(self, owner, is_public, name=None):
        resource = ExampleRestrictedResource.objects.create(
            owner = owner, is_public = is_public, name=name)
        self.addCleanup(resource.delete)
        return resource

    def add_resources(self, resources, owner, is_public):
        for name in resources:
            self.getUniqueResource(
                name=name, owner=owner, is_public=is_public)
