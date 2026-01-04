from django.test import TestCase
from django.contrib.auth import get_user_model
from app_expenses.models import Category
from django.core.exceptions import ValidationError, PermissionDenied

User = get_user_model()

class CategoryModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(username="user1")
        self.user2 = User.objects.create(username="user2")
        
    # ------------ Missing field ---------------

    def test_category_with_missing_user_fails(self):
        """Category: fails when 'user' is missing"""
        category = Category(name="Food")
        with self.assertRaisesMessage(ValidationError, "User does not exists."):
            category.full_clean()

    def test_category_with_missing_name_fails(self):
        """Category: fails when 'name' is missing"""
        category = Category(user=self.user1)
        with self.assertRaisesMessage(ValidationError, "Name is required."):
            category.full_clean()

    # ---------- Non existing User --------------

    def test_category_with_non_existing_user_fails(self):
        """Category: fails with non existing 'user'"""
        non_existing_user = User(username="not-exists")
        category = Category(user=non_existing_user, name="Food")
        with self.assertRaises(ValidationError):
            category.full_clean()

    # ----------- Predefined categories ------------

    def test_category_create_predefined_fails(self):
        """Category: fails to create pre-defined category(user=None)."""
        predefined = Category(user=None, name="Food")
        with self.assertRaisesMessage(PermissionDenied, "Data is predefined and not owned."):
            predefined.create_by(self.user1)  

    def test_category_fetch_predefined_success(self):
        """Category: success to fetch pre-defined categories, should return only user=None entries."""
        Category.objects.create(user=None, name="Food")
        predefined_category = Category.objects.filter(user=None).first()
        print("PRED : ", predefined_category)
        if not predefined_category:
            raise Category.DoesNotExist
        self.assertIsNone(predefined_category.user)

    def test_category_update_predefined_fails(self):
        """Category: fails to update pre-defined categories(user=None)."""
        predefined = Category.objects.create(user=None, name="Food")
        predefined.name = "Travel"
        with self.assertRaisesMessage(PermissionDenied, "Data is predefined and not owned."):
            predefined.update_by(self.user1)

    # ------------ Uniqueness ------------

    def test_category_duplicate_name_same_user_fails(self):
        """Category: fails when duplicate 'name' (case-insensitive) exists for same user"""
        Category.objects.create(user=self.user1, name="Food")
        duplicate = Category(user=self.user1, name="FOOD")
        with self.assertRaisesMessage(ValidationError, f"Category with Name: '{duplicate.name}' already exists."):
            duplicate.full_clean()

    def test_category_duplicate_name_different_user_success(self):
        """Category: succeeds when duplicate 'name' exists for different users"""
        Category.objects.create(user=self.user1, name="Food")
        category = Category(user=self.user2, name="Food")
        category.full_clean()

    def test_category_duplicate_name_as_predefined_fails(self):
        """Category: fails when duplicate predefined 'name' (case-insensitive) exists."""
        predefined = Category.objects.create(user=None, name="Food")
        duplicate = Category(user=self.user1, name="FOOD")
        with self.assertRaisesMessage(ValidationError, f"Predefined category with Name: '{duplicate.name}' already exists."):
            duplicate.full_clean()

    def test_category_update_to_duplicate_name_same_user_fails(self):
        """Category: fails when updating to duplicate 'name' for same user"""
        category1 = Category.objects.create(user=self.user1, name="Food")
        category2 = Category.objects.create(user=self.user1, name="Gym")
        category2.name = "Food"
        with self.assertRaisesMessage(ValidationError, f"Category with Name: '{category2.name}' already exists."):
            category2.full_clean()

    # ---------- Whitespace Normalization ----------

    def test_category_whitespace_trimmed_success(self):
        """Category: success to trim leading/trailing whitespace."""
        category = Category(user=self.user1, name="   Gym   ")
        category.create_by(self.user1)
        self.assertEqual(category.name, "Gym")

    def test_category_name_with_whitespace_only_fails(self):
        """Category: fails when 'name' is only whitespace"""
        category = Category(user=self.user1, name="   ")
        with self.assertRaisesMessage(ValidationError, "Name cannot be blank or whitespace."):
            category.full_clean()

    # ----------- Character limit -------------

    def test_category_name_exceeded_max_length_fails(self):
        """Category: fails with exceeding max_length 'name'."""
        with self.assertRaises(ValidationError):
            category = Category(user=self.user1, name="x" * 121)
            category.create_by(self.user1)

    # ----------- Valid owned data ----------------

    def test_category_create_with_valid_values_success(self):
        """Category: success to create with valid 'user', 'name'"""
        category = Category(user=self.user1, name="Food")
        category = category.create_by(self.user1)
        self.assertEqual(category.name, "Food")
        self.assertEqual(category.user, self.user1)

    def test_category_fetch_owned_success(self):
        """Category: success to fetch owned category."""
        category = Category.objects.create(user=self.user1, name="Food")
        fetched = Category.get_for_user(self.user1, category.pk)
        self.assertEqual(fetched.pk, category.pk)
    
    def test_category_update_owned_success(self):
        """Category: success to update owned category."""
        category = Category.objects.create(user=self.user1, name="Food")
        category.name = "Home Rent"
        category.update_by(self.user1)
        self.assertEqual(category.name, "Home Rent")
    
    # ----------- Others owned data ---------------

    def test_category_fetch_others_owned_fails(self):
        """Category: fail to fetch others owned category."""
        category = Category.objects.create(user=self.user2, name="Food")
        with self.assertRaisesMessage(PermissionDenied, "You are not the owner."):
            Category.get_for_user(self.user1, category.pk)

    def test_category_update_others_owned_fails(self):
        """Category: fail to update others owned category."""
        category = Category.objects.create(user=self.user2, name="Food")
        category.name = "Travel"
        with self.assertRaisesMessage(PermissionDenied, "You are not the owner."):
            category.update_by(self.user1)
