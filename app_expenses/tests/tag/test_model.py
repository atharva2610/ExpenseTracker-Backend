from django.test import TestCase
from django.contrib.auth import get_user_model
from app_expenses.models import Tag
from django.core.exceptions import ValidationError, PermissionDenied

User = get_user_model()

class TagModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(username="user1")
        self.user2 = User.objects.create(username="user2")
        
    # ------------ Missing field ---------------

    def test_tag_with_missing_user_fails(self):
        """Tag: fails when 'user' is missing"""
        tag = Tag(name="Food")
        with self.assertRaisesMessage(ValidationError, "User does not exists."):
            tag.full_clean()

    def test_tag_with_missing_name_fails(self):
        """Tag: fails when 'name' is missing"""
        tag = Tag(user=self.user1)
        with self.assertRaisesMessage(ValidationError, "Name is required."):
            tag.full_clean()

    # ---------- Non existing User --------------

    def test_tag_with_non_existing_user_fails(self):
        """Tag: fails with non existing 'user'"""
        non_existing_user = User(username="not-exists")
        tag = Tag(user=non_existing_user, name="Food")
        with self.assertRaises(ValidationError):
            tag.full_clean()

    # ------------ Uniqueness (case‑insensitive) ------------

    def test_tag_duplicate_name_same_user_fails(self):
        """Tag: fails when duplicate 'name' (case-insensitive) exists for same user"""
        Tag.objects.create(user=self.user1, name="Food")
        duplicate = Tag(user=self.user1, name="FOOD")
        with self.assertRaisesMessage(ValidationError, f"Tag with Name: '{duplicate.name}' already exists."):
            duplicate.full_clean()

    def test_tag_duplicate_name_different_users_success(self):
        """Tag: succeeds when duplicate 'name' exists for different users"""
        Tag.objects.create(user=self.user1, name="Food")
        tag = Tag(user=self.user2, name="Food")
        tag.full_clean()

    def test_tag_update_to_duplicate_name_same_user_fails(self):
        """Tag: fails when updating to duplicate 'name' for same user"""
        tag1 = Tag.objects.create(user=self.user1, name="Food")
        tag2 = Tag.objects.create(user=self.user1, name="Gym")
        tag2.name = "Food"
        with self.assertRaisesMessage(ValidationError, f"Tag with Name: '{tag2.name}' already exists."):
            tag2.full_clean()

    # ---------- Whitespace Normalization ----------

    def test_tag_whitespace_trimmed_success(self):
        """Tag: success to trim leading/trailing whitespace."""
        tag = Tag(user=self.user1, name="   Cash   ")
        tag.create_by(self.user1)
        self.assertEqual(tag.name, "Cash")

    def test_tag_name_with_whitespace_only_fails(self):
        """Tag: fails when 'name' is only whitespace"""
        tag = Tag(user=self.user1, name="   ")
        with self.assertRaisesMessage(ValidationError, "Name cannot be blank or whitespace."):
            tag.full_clean()

    # ----------- Character limit -------------

    def test_tag_name_exceeded_max_length_fails(self):
        """Tag: fails with exceeding max_length 'name'."""
        with self.assertRaises(ValidationError):
            tag = Tag(user=self.user1, name="x" * 65)
            tag.create_by(self.user1)

    # ----------- Valid owned data ----------------

    def test_tag_create_with_valid_values_success(self):
        """Tag: success to create with valid 'user', 'name'"""
        tag = Tag(user=self.user1, name="Food")
        tag = tag.create_by(self.user1)
        self.assertEqual(tag.name, "Food")
        self.assertEqual(tag.user, self.user1)

    def test_tag_fetch_owned_success(self):
        """Tag: success to fetch owned Tag."""
        tag = Tag.objects.create(user=self.user1, name="Food")
        fetched = Tag.get_for_user(self.user1, tag.pk)
        self.assertEqual(fetched.pk, tag.pk)
    
    def test_tag_update_owned_success(self):
        """Tag: success to update owned Tag."""
        tag = Tag.objects.create(user=self.user1, name="Food")
        tag.name = "Home Rent"
        tag.update_by(self.user1)
        self.assertEqual(tag.name, "Home Rent")

    # ----------- Others owned data ---------------

    def test_tag_fetch_others_owned_fails(self):
        """Tag: fail to fetch others owned tag."""
        tag = Tag.objects.create(user=self.user2, name="Food")
        with self.assertRaisesMessage(PermissionDenied, "You are not the owner."):
            Tag.get_for_user(self.user1, tag.pk)

    def test_tag_update_others_owned_fails(self):
        """Tag: fail to update others owned tag."""
        tag = Tag.objects.create(user=self.user2, name="Food")
        tag.name = "Travel"
        with self.assertRaisesMessage(PermissionDenied, "You are not the owner."):
            tag.update_by(self.user1)

