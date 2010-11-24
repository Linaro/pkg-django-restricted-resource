"""
Unit tests for django_restricted_resource application
"""

from django.contrib.auth.models import (AnonymousUser, User, Group)
from django.core.exceptions import ValidationError

from django_testscenarios import TestCaseWithScenarios
from django_restricted_resource.test_utils import (
    ExampleRestrictedResource,
    FixtureHelper,
    TestCase,
    TestCaseWithInvariants,
    TestCaseWithScenarios,
)

from django_restricted_resource.models import RestrictedResource



class ResourceCleanTests(TestCase, FixtureHelper):

    def test_clean_raises_exception_when_owner_is_not_set(self):
        resource = RestrictedResource()
        self.assertRaises(ValidationError, resource.clean)

    def test_clean_raises_exception_when_both_user_and_group_is_set(self):
        user = self.getUniqueUser()
        group = self.getUniqueGroup()
        resource = RestrictedResource(user=user, group=group)
        self.assertRaises(ValidationError, resource.clean)

    def test_clean_is_okay_when_just_user_set(self):
        user = self.getUniqueUser()
        resource = RestrictedResource(user=user)
        self.assertEqual(resource.clean(), None)

    def test_clean_is_okay_when_just_group_set(self):
        group = self.getUniqueGroup()
        resource = RestrictedResource(group=group)
        self.assertEqual(resource.clean(), None)


class ResourceOwnerTest(TestCase, FixtureHelper):
    """ Tests for the owner property """

    def test_user_is_owner(self):
        user = self.getUniqueUser()
        resource = ExampleRestrictedResource(user=user)
        self.assertEqual(resource.owner, user)

    def test_group_is_owner(self):
        group = self.getUniqueGroup()
        resource = ExampleRestrictedResource(group=group)
        self.assertEqual(resource.owner, group)

    def test_owner_can_be_changed_to_group(self):
        group = self.getUniqueGroup()
        resource = ExampleRestrictedResource()
        resource.owner = group
        resource.save()
        self.assertEqual(resource.group, group)
        self.assertEqual(resource.user, None)

    def test_owner_can_be_changed_to_user(self):
        user = self.getUniqueUser()
        resource = ExampleRestrictedResource()
        resource.owner = user
        resource.save()
        self.assertEqual(resource.group, None)
        self.assertEqual(resource.user, user)


class OthersDoNotOwnResource(
    TestCaseWithInvariants, FixtureHelper):
    """
    RestrictedResource.is_owned_by() returns False for everyone but the owner
    """
    invariants = dict(
        owner = dict(
            user = lambda self: self.getUniqueUser(),
            group = lambda self: self.getUniqueGroup(),
        ),
        accessing_principal = dict(
            nothing = None,
            anonymous_user = AnonymousUser(),
            inactive_user = lambda self: self.getUniqueUser(is_active=False),
            unrelated_user = lambda self: self.getUniqueUser(),
            unrelated_group = lambda self: self.getUniqueGroup(),
        ),
        is_public = [True, False],
    )

    def test(self):
        resource = self.getUniqueResource(
            owner=self.owner, is_public=self.is_public)
        self.assertFalse(
            resource.is_owned_by(self.accessing_principal))


class OwnerOwnsResource(
    TestCaseWithInvariants, FixtureHelper):
    """
    RestrictedResource.is_owned_by() returns True for the owner
    """

    invariants = dict(
        owner = dict(
            user = lambda self: self.getUniqueUser(),
            group = lambda self: self.getUniqueGroup(),
        ),
        is_public = [True, False],
    )

    def test(self):
        resource = self.getUniqueResource(
            owner=self.owner, is_public=self.is_public)
        self.assertTrue(resource.is_owned_by(self.owner))


class ResourceManagerOwnerSetFindsNoMatchesForOthers(
    TestCaseWithInvariants, FixtureHelper):
    """
    RestrictedResourceManager.owned_by_principal() does not return
    anything for non-owners
    """

    invariants = dict(
        owner = dict(
            user = lambda self: self.getUniqueUser(),
            group = lambda self: self.getUniqueGroup(),
        ),
        accessing_principal = dict(
            nothing = None,
            anonymous_user = AnonymousUser(),
            inactive_user = lambda self: self.getUniqueUser(is_active=False),
            unrelated_user = lambda self: self.getUniqueUser(),
            unrelated_group = lambda self: self.getUniqueGroup(),
        ),
        is_public = [True, False],
    )

    def test(self):
        manager = ExampleRestrictedResource.objects
        resource = self.getUniqueResource(
            owner=self.owner, is_public=self.is_public)
        result = manager.owned_by_principal(self.accessing_principal)
        self.assertEqual(result.count(), 0)


class ResourceManagerOwnerSetFindsMatchesForOwner(
    TestCaseWithInvariants, FixtureHelper):

    invariants = dict(
        num_objects = [0, 10, 500],
        owner = dict(
            user = lambda self: self.getUniqueUser(),
            group = lambda self: self.getUniqueGroup(),
        ),
        is_public = [True, False],
    )

    def test(self):
        for i in range(self.num_objects):
            self.getUniqueResource(
                owner=self.owner,
                name=str(i),
                is_public=self.is_public)
        manager = ExampleRestrictedResource.objects
        result = manager.owned_by_principal(self.owner)
        self.assertEqual(result.count(), self.num_objects)


class EveryoneHasPublicAccessToPublicResources(
    TestCaseWithInvariants, FixtureHelper):
    """ Tests for the get_access_type() method """

    invariants = dict(
        owner = dict(
            user = lambda self: self.getUniqueUser(),
            group = lambda self: self.getUniqueGroup(),
        ),
        accessing_principal = dict(
            nothing = None,
            anonymous_user = AnonymousUser(),
            inactive_user = lambda self: self.getUniqueUser(is_active=False),
            unrelated_user = lambda self: self.getUniqueUser(),
            unrelated_group = lambda self: self.getUniqueGroup(),
            owner = lambda self: self.owner,
        ),
        is_public = [True, False],
    )

    def test(self):
        resource = self.getUniqueResource(
            owner=self.owner, is_public=True)
        self.assertEqual(
            resource.get_access_type(self.accessing_principal),
            resource.PUBLIC_ACCESS)


class NobodyButTheOwnerHasAccessToNonPublicUserResources(
    TestCaseWithInvariants, FixtureHelper):
    """ Tests for the get_access_type() method """

    invariants = dict(
        accessing_principal = dict(
            nothing = None,
            anonymous_user = AnonymousUser(),
            inactive_user = lambda self: self.getUniqueUser(is_active=False),
            unrelated_user = lambda self: self.getUniqueUser(),
            unrelated_group = lambda self: self.getUniqueGroup(),
        )
    )

    def test_everyone_else(self):
        owner = self.getUniqueUser()
        resource = self.getUniqueResource(is_public=False, owner=owner)
        self.assertEqual(
            resource.get_access_type(self.accessing_principal),
            resource.NO_ACCESS)


class OwnerHasPrivateAccessToNonPublicUserResources(
    TestCase, FixtureHelper):
    """ Tests for the get_access_type() method """

    def test_owner(self):
        owner = self.getUniqueUser()
        resource = self.getUniqueResource(is_public=False, owner=owner)
        self.assertEqual(
            resource.get_access_type(owner),
            resource.PRIVATE_ACCESS)


class GroupMembersGetSharedAccessToNonPublicGroupResources(
    TestCase, FixtureHelper):

    def test_get_access_type_for_owning_group(self):
        owner = self.getUniqueGroup()
        resource = self.getUniqueResource(owner=owner, is_public=False)
        self.assertEqual(
            resource.get_access_type(owner),
            resource.SHARED_ACCESS)

    def test_get_access_type_for_related_user(self):
        owner = self.getUniqueGroup()
        resource = self.getUniqueResource(owner=owner, is_public=False)
        related_user = self.getUniqueUser()
        related_user.groups.add(owner)
        self.assertEqual(
            resource.get_access_type(related_user),
            resource.SHARED_ACCESS)


class ManagerAccessibilityTests(TestCaseWithScenarios, FixtureHelper):

    def setUp(self):
        super(ManagerAccessibilityTests, self).setUp()
        self.user = self.getUniqueUser()
        self.unrealted_group = self.getUniqueGroup()
        self.group = self.getUniqueGroup()
        self.unrelated_user = self.getUniqueUser()
        self.manager = ExampleRestrictedResource.objects

    def add_resources(self, resources, owner, is_public):
        for name in resources:
            self.getUniqueResource(
                name=name, owner=owner, is_public=is_public)

    def test_accessible_by_anyone_returns_only_public_objects(self):
        self.add_resources(["a", "b", "c"], owner=self.user, is_public=True)
        self.add_resources(["x", "y", "z"], owner=self.user, is_public=False)
        resources = self.manager.accessible_by_anyone()
        self.assertEqual(
            [res.name for res in resources],
            ["a", "b", "c"])

    def test_accessible_by_prinipal_for_owner(self):
        self.add_resources(["a", "b", "c"], owner=self.user, is_public=True)
        self.add_resources(["x", "y", "z"], owner=self.user, is_public=False)
        resources = self.manager.accessible_by_principal(self.user)
        self.assertEqual(
            [res.name for res in resources],
            ["a", "b", "c", "x", "y", "z"])

    def test_accessible_by_prinipal_for_owner(self):
        self.add_resources(["a", "b", "c"], owner=self.user, is_public=True)
        self.add_resources(["x", "y", "z"], owner=self.user, is_public=False)
        resources = self.manager.accessible_by_principal(self.user)
        self.assertEqual(
            [res.name for res in resources],
            ["a", "b", "c", "x", "y", "z"])

    def test_accessible_by_prinicpal_for_unrelated_user(self):
        self.add_resources(["a", "b", "c"], owner=self.user, is_public=True)
        self.add_resources(["x", "y", "z"], owner=self.user, is_public=False)
        resources = self.manager.accessible_by_principal(self.unrelated_user)
        self.assertEqual(
            [res.name for res in resources],
            ["a", "b", "c"])

    def test_accessible_by_prinicpal_for_unrelated_user_without_any_public_objects(self):
        self.add_resources(["x", "y", "z"], owner=self.user, is_public=False)
        resources = self.manager.accessible_by_principal(self.unrelated_user)
        self.assertEqual([res.name for res in resources], [])

    def test_accessible_by_principal_for_group(self):
        self.add_resources(["a", "b", "c"], owner=self.group, is_public=True)
        self.add_resources(["x", "y", "z"], owner=self.group, is_public=False)
        resources = self.manager.accessible_by_principal(self.unrelated_user)
        self.assertEqual([res.name for res in resources], ["a", "b", "c"])

    def test_accessible_by_principal_for_group_and_member(self):
        self.add_resources(["a", "b", "c"], owner=self.group, is_public=True)
        self.add_resources(["x", "y", "z"], owner=self.group, is_public=False)
        self.user.groups.add(self.group)
        resources = self.manager.accessible_by_principal(self.user)
        self.assertEqual(
            [res.name for res in resources],
            ["a", "b", "c", "x", "y", "z"])


