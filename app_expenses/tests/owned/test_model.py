from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from app_expenses.models import Category  # or any model inheriting OwnedModel

User = get_user_model()

class OwnedModelTest(TestCase):
    def setUp(self):
        # Create two users
        self.user1 = User.objects.create(username="user1")
        self.user2 = User.objects.create(username="user2")

        # Predefined object (no owner)
        self.predefined = Category.objects.create(name="Predefined", user=None)

        # Owned object
        self.owned = Category.objects.create(name="Owned", user=self.user1)

    # ---------- create_by() tests -----------------

    def test_create_by_without_user_and_requested_user_fails(self):
        """create_by: fails when neither 'user' nor requested_user is provided"""
        obj = Category(name="Test")
        with self.assertRaises(PermissionDenied):
            obj.create_by(None)

    def test_create_by_with_user_not_matching_requested_user_fails(self):
        """create_by: fails when 'user' is set but does not match requested_user"""
        obj = Category(name="Test", user=self.user1)
        with self.assertRaises(PermissionDenied):
            obj.create_by(self.user2)

    def test_create_by_without_user_uses_requested_user_success(self):
        """create_by: succeeds when 'user' is None and requested_user is provided"""
        obj = Category(name="Test")
        result = obj.create_by(self.user1)
        self.assertEqual(result.user, self.user1)

    def test_create_by_on_existing_object_fails(self):
        """create_by: fails when called on an already saved object"""
        with self.assertRaises(PermissionDenied):
            self.owned.create_by(self.user1)

    def test_create_by_with_user_different_from_requested_user_fails(self):
        """create_by: fails when 'user' is set to a different user than requested_user"""
        obj = Category(name="Test", user=self.user2)
        with self.assertRaises(PermissionDenied):
            obj.create_by(self.user1)

    # ------------ update_by() tests ---------------

    def test_update_by_on_unsaved_object_fails(self):
        """update_by: fails when called on a new unsaved object"""
        obj = Category(name="Unsaved")
        with self.assertRaises(PermissionDenied):
            obj.update_by(self.user1)

    def test_update_by_without_requested_user_fails(self):
        """update_by: fails when requested_user is not provided"""
        with self.assertRaises(PermissionDenied):
            self.owned.update_by(None)

    def test_update_by_on_predefined_object_fails(self):
        """update_by: fails when object has no owner (predefined data)"""
        with self.assertRaises(PermissionDenied):
            self.predefined.update_by(self.user1)

    def test_update_by_with_wrong_user_fails(self):
        """update_by: fails when requested_user is not the owner"""
        with self.assertRaises(PermissionDenied):
            self.owned.update_by(self.user2)

    def test_update_by_with_correct_owner_success(self):
        """update_by: succeeds when requested_user is the correct owner"""
        self.owned.name = "Updated"
        result = self.owned.update_by(self.user1)
        self.assertEqual(result.name, "Updated")

    # ------------- get_for_user() tests --------------

    def test_get_for_user_without_requested_user_fails(self):
        """get_for_user: fails when requested_user is not provided"""
        with self.assertRaises(PermissionDenied):
            Category.get_for_user(None, self.owned.pk)

    def test_get_for_user_on_predefined_object_success(self):
        """get_for_user: succeeds when fetching predefined object (user=None)"""
        result = Category.get_for_user(self.user1, self.predefined.pk)
        self.assertEqual(result, self.predefined)

    def test_get_for_user_on_owned_object_success(self):
        """get_for_user: succeeds when requested_user is the owner"""
        result = Category.get_for_user(self.user1, self.owned.pk)
        self.assertEqual(result, self.owned)

    def test_get_for_user_on_other_users_object_fails(self):
        """get_for_user: fails when requested_user is not the owner"""
        with self.assertRaises(PermissionDenied):
            Category.get_for_user(self.user2, self.owned.pk)

    # ------------- delete_by() tests --------------

    def test_delete_by_without_requested_user_fails(self):
        """delete_by: fails when requested_user is not provided"""
        with self.assertRaises(PermissionDenied):
            self.owned.delete_by(None)

    def test_delete_by_on_unsaved_object_fails(self):
        """delete_by: fails when called on a new unsaved object"""
        obj = Category(name="Unsaved")
        with self.assertRaises(PermissionDenied):
            obj.delete_by(self.user1)

    def test_delete_by_owned_data_success(self):
        """delete_by: succeeds when requested_user is the owner"""
        pk = self.owned.pk
        deleted_count, _ = self.owned.delete_by(self.user1)
        # Assert deletion tuple
        self.assertEqual(deleted_count, 1)
        self.assertFalse(Category.objects.filter(pk=pk).exists())

    def test_delete_by_other_users_data_fails(self):
        """delete_by: fails when requested_user is not the owner"""
        with self.assertRaises(PermissionDenied):
            self.owned.delete_by(self.user2)

    def test_delete_by_on_predefined_object_fails(self):
        """delete_by: fails when object has no owner (predefined data)"""
        with self.assertRaises(PermissionDenied):
            self.predefined.delete_by(self.user1)