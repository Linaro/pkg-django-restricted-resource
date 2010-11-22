"""
Unit tests for django_restricted_resource application
"""

from django.contrib.auth.models import (AnonymousUser, User, Group)
from django.core.exceptions import ValidationError
from django.db import models

from django_testscenarios import TestCaseWithScenarios

from django_restricted_resource.models import RestrictedResource


class ExampleRestrictedResource(RestrictedResource):
    """
    Dummy model to get non-abstract model that inherits from
    RestrictedResource
    """
    name = models.CharField(max_length=100, null=True)


class ResourceCleanTests(TestCaseWithScenarios):

    def setUp(self):
        self.user = User.objects.create(username='user')
        self.group = Group.objects.create(name='group')

    def tearDown(self):
        self.user.delete()
        self.group.delete()

    def test_clean_raises_exception_when_owner_is_not_set(self):
        resource = RestrictedResource()
        self.assertRaises(ValidationError, resource.clean)

    def test_clean_raises_exception_when_both_user_and_group_is_set(self):
        resource = RestrictedResource(user=self.user, group=self.group)
        self.assertRaises(ValidationError, resource.clean)

    def test_clean_is_okay_when_just_user_set(self):
        resource = RestrictedResource(user=self.user)
        self.assertEqual(resource.clean(), None)

    def test_clean_is_okay_when_just_group_set(self):
        resource = RestrictedResource(group=self.group)
        self.assertEqual(resource.clean(), None)


class ResourceOwnerTest(TestCaseWithScenarios):
    """ Tests for the owner property """

    def setUp(self):
        self.user = User.objects.create(username="user")
        self.group = Group.objects.create(name="group")

    def tearDown(self):
        self.user.delete()
        self.group.delete()

    def test_user_is_owner(self):
        resource = ExampleRestrictedResource(user=self.user)
        self.assertEqual(resource.owner, self.user)

    def test_group_is_owner(self):
        resource = ExampleRestrictedResource(group=self.group)
        self.assertEqual(resource.owner, self.group)

    def test_owner_can_be_changed_to_group(self):
        resource = ExampleRestrictedResource()
        resource.owner = self.group
        resource.save()
        self.assertEqual(resource.group, self.group)
        self.assertEqual(resource.user, None)

    def test_owner_can_be_changed_to_user(self):
        resource = ExampleRestrictedResource()
        resource.owner = self.user
        resource.save()
        self.assertEqual(resource.group, None)
        self.assertEqual(resource.user, self.user)


class CommonScenarios(object):

    scenarios = [
        ('public_resource_owned_by_user', {
            'owned_by': 'user',
            'is_public': True,
        }),
        ('public_resource_owned_by_group', {
            'owned_by': 'group',
            'is_public': True,
        }),
        ('private_resource_owned_by_user', {
            'owned_by': 'user',
            'is_public': False,
        }),
        ('private_resource_owned_by_group', {
            'owned_by': 'group',
            'is_public': False,
        }),
    ]

    def setUp(self):
        super(CommonScenarios, self).setUp()
        if self.owned_by == 'user':
            self.owner = User.objects.create(username='user')
        else:
            self.owner = Group.objects.create(name='group')
        self.resource = ExampleRestrictedResource(is_public=self.is_public)
        self.resource.owner = self.owner
        self.resource.save()
        self.unrelated_group = Group.objects.create(name='unrelated group')
        self.unrelated_user = User.objects.create(username='unrelated user')
        self.blocked_user = User.objects.create(username='blocked user',
                                                is_active=False)
        self.anonymous_user = AnonymousUser()

    def tearDown(self):
        super(CommonScenarios, self).tearDown()
        self.blocked_user.delete()
        self.unrelated_user.delete()
        self.unrelated_group.delete()
        self.resource.delete()
        self.owner.delete()


class ResourceOwnershipTests(CommonScenarios, TestCaseWithScenarios):
    """Tests for the owner property"""

    def test_not_owned_by_nobody(self):
        self.assertEqual(
            self.resource.is_owned_by(None), False)

    def test_not_owned_by_blocked_user(self):
        self.assertEqual(
            self.resource.is_owned_by(self.blocked_user), False)

    def test_not_owned_by_anonymous_user(self):
        self.assertEqual(
            self.resource.is_owned_by(self.anonymous_user), False)

    def test_not_owned_by_unrelated_user(self):
        self.assertEqual(
            self.resource.is_owned_by(self.unrelated_user),
            False)

    def test_not_owned_by_unrelated_group(self):
        self.assertEqual(
            self.resource.is_owned_by(self.unrelated_user),
            False)

    def test_owned_by_owner(self):
        self.assertEqual(self.resource.is_owned_by(self.owner), True)


class ResourceAccessibilityTests(CommonScenarios, TestCaseWithScenarios):
    """Tests for the is_accessible_by() method"""

    def test_accessible_by_nobody(self):
        self.assertEqual(
            self.resource.is_accessible_by(None),
            self.is_public)

    def test_accessible_by_anonymous_user(self):
        self.assertEqual(
            self.resource.is_accessible_by(self.anonymous_user),
            self.is_public)

    def test_accessible_by_blocked_user(self):
        self.assertEqual(
            self.resource.is_accessible_by(self.blocked_user),
            self.is_public)

    def test_accessible_by_unrelated_user(self):
        self.assertEqual(
            self.resource.is_accessible_by(self.unrelated_user),
            self.is_public)

    def test_accessible_by_unrelated_group(self):
        self.assertEqual(
            self.resource.is_accessible_by(self.unrelated_group),
            self.is_public)

    def test_accessible_by_owner(self):
        self.assertEqual(
            self.resource.is_accessible_by(self.owner),
            True)


class PublicResourceAccessibilityTypeTests(TestCaseWithScenarios):
    """ Tests for the get_access_type() method """

    scenarios = [
        ('resource_owned_by_user', {
            'owned_by': 'user',
        }),
        ('resource_owned_by_group', {
            'owned_by': 'group',
        }),
    ]

    def setUp(self):
        super(PublicResourceAccessibilityTypeTests, self).setUp()
        if self.owned_by == 'user':
            self.owner = User.objects.create(username='user')
        else:
            self.owner = Group.objects.create(name='group')
        self.resource = ExampleRestrictedResource(is_public=True)
        self.resource.owner = self.owner
        self.resource.save()
        self.unrelated_group = Group.objects.create(name='unrelated group')
        self.unrelated_user = User.objects.create(username='unrelated user')
        self.blocked_user = User.objects.create(username='blocked user',
                                                is_active=False)
        self.anonymous_user = AnonymousUser()

    def tearDown(self):
        super(PublicResourceAccessibilityTypeTests, self).tearDown()
        self.blocked_user.delete()
        self.unrelated_user.delete()
        self.unrelated_group.delete()
        self.resource.delete()
        self.owner.delete()

    def test_get_access_type_for_nobody(self):
        self.assertEqual(
            self.resource.get_access_type(None),
            self.resource.PUBLIC_ACCESS)

    def test_get_access_type_for_blocked_user(self):
        self.assertEqual(
            self.resource.get_access_type(self.blocked_user),
            self.resource.PUBLIC_ACCESS)

    def test_get_access_type_for_anonymous_user(self):
        self.assertEqual(
            self.resource.get_access_type(self.anonymous_user),
            self.resource.PUBLIC_ACCESS)

    def test_get_access_type_for_unrelated_user(self):
        self.assertEqual(
            self.resource.get_access_type(self.unrelated_user),
            self.resource.PUBLIC_ACCESS)

    def test_get_access_type_for_unrelated_group(self):
        self.assertEqual(
            self.resource.get_access_type(self.unrelated_user),
            self.resource.PUBLIC_ACCESS)

    def test_access_type_for_owner(self):
        self.assertEqual(
            self.resource.get_access_type(self.owner),
            self.resource.PUBLIC_ACCESS)


class PrivateResourceAccessibilityTypeRejectionTests(TestCaseWithScenarios):
    """ Tests for the get_access_type() method """

    scenarios = [
        ('resource_owned_by_user', {
            'owned_by': 'user',
        }),
        ('resource_owned_by_group', {
            'owned_by': 'group',
        }),
    ]

    def setUp(self):
        super(PrivateResourceAccessibilityTypeRejectionTests, self).setUp()
        if self.owned_by == 'user':
            self.owner = User.objects.create(username='user')
        else:
            self.owner = Group.objects.create(name='group')
        self.resource = ExampleRestrictedResource(is_public=False)
        self.resource.owner = self.owner
        self.resource.save()
        self.unrelated_group = Group.objects.create(name='unrelated group')
        self.unrelated_user = User.objects.create(username='unrelated user')
        self.blocked_user = User.objects.create(username='blocked user',
                                                is_active=False)
        self.anonymous_user = AnonymousUser()

    def tearDown(self):
        super(PrivateResourceAccessibilityTypeRejectionTests, self).setUp()
        self.blocked_user.delete()
        self.unrelated_user.delete()
        self.unrelated_group.delete()
        self.resource.delete()
        self.owner.delete()

    def test_get_access_type_for_nobody(self):
        self.assertEqual(
            self.resource.get_access_type(None),
            self.resource.NO_ACCESS)

    def test_get_access_type_for_blocked_user(self):
        self.assertEqual(
            self.resource.get_access_type(self.blocked_user),
            self.resource.NO_ACCESS)

    def test_get_access_type_for_anonymous_user(self):
        self.assertEqual(
            self.resource.get_access_type(self.anonymous_user),
            self.resource.NO_ACCESS)

    def test_get_access_type_for_unrelated_user(self):
        self.assertEqual(
            self.resource.get_access_type(self.unrelated_user),
            self.resource.NO_ACCESS)

    def test_get_access_type_for_unrelated_group(self):
        self.assertEqual(
            self.resource.get_access_type(self.unrelated_user),
            self.resource.NO_ACCESS)


class PrivateResourceAccessibilityTypeTests(TestCaseWithScenarios):

    def setUp(self):
        super(PrivateResourceAccessibilityTypeTests, self).setUp()
        self.owning_user = User.objects.create(username='user')
        self.resource = ExampleRestrictedResource.objects.create(
            user=self.owning_user, is_public=False)

    def tearDown(self):
        super(PrivateResourceAccessibilityTypeTests, self).tearDown()
        self.resource.delete()
        self.owning_user.delete()

    def test_get_access_type_for_owning_user(self):
        self.assertEqual(
            self.resource.get_access_type(self.owning_user),
            self.resource.PRIVATE_ACCESS)


class SharedResourceAccessibilityTypeTests(TestCaseWithScenarios):

    def setUp(self):
        super(SharedResourceAccessibilityTypeTests, self).setUp()
        self.owning_group = Group.objects.create(name='group')
        self.related_user = User.objects.create(username='user')
        self.related_user.groups.add(self.owning_group)
        self.resource = ExampleRestrictedResource.objects.create(
            group=self.owning_group, is_public=False)

    def tearDown(self):
        super(SharedResourceAccessibilityTypeTests, self).tearDown()
        self.resource.delete()
        self.owning_group.delete()
        self.related_user.delete()

    def test_get_access_type_for_owning_group(self):
        self.assertEqual(
            self.resource.get_access_type(self.owning_group),
            self.resource.SHARED_ACCESS)

    def test_get_access_type_for_related_user(self):
        self.assertEqual(
            self.resource.get_access_type(self.related_user),
            self.resource.SHARED_ACCESS)
