from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, PermissionDenied
from app_expenses.models import Shortcut, Currency, FundAccount, Category, TransactionType

User = get_user_model()

class ShortcutModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(username="user1")
        self.user2 = User.objects.create(username="user2")
        self.category = Category.objects.create(user=self.user1, name="Food")
        self.currency = Currency.objects.create(id="INR", symbol="₹", name="Indian Rupee")
        self.fund_account = FundAccount.objects.create(user=self.user1, name="Bank", currency=self.currency, balance=5000)

    # ----------- Missing field---------------

    def test_shortcut_with_missing_user_fails(self):
        """Shortcut: fails when 'user' is missing"""
        shortcut = Shortcut(
            name = "Salary",
            amount = 40000,
            fund_account = self.fund_account,
            type = TransactionType.CREDIT
        )
        with self.assertRaisesMessage(ValidationError, "User does not exists."):
            shortcut.full_clean()

    def test_shortcut_with_missing_name_fails(self):
        """Shortcut: fails when 'name' is missing"""
        shortcut = Shortcut(
            user = self.user1,
            amount = 40000,
            fund_account = self.fund_account,
            type = TransactionType.CREDIT
        )
        with self.assertRaisesMessage(ValidationError, "Name is required."):
            shortcut.full_clean()

    def test_shortcut_with_missing_type_success(self):
        """Shortcut: success to set default 'type' debit when 'type' is missing"""
        shortcut = Shortcut.objects.create(
            user = self.user1,
            name = "EMI",
            amount = 4000,
            fund_account = self.fund_account,
        )
        self.assertEqual(shortcut.type, TransactionType.DEBIT)

    def test_shortcut_with_missing_amount_success(self):
        """Shortcut: success to set default zero when 'amount' is missing"""
        shortcut = Shortcut(
            user = self.user1,
            name = "Tax"
        )
        self.assertEqual(shortcut.amount, 0)

    # ---------- Non existing User/Category/Fund Account --------------

    def test_shortcut_with_non_existing_user_fails(self):
        """Shortcut: fails to create with non existing 'user'"""
        non_existing_user = User(username="new_user")
        shortcut = Shortcut(
            user = non_existing_user,
            name = "Tax"
        )
        with self.assertRaisesMessage(ValidationError, "User does not exists."):
            shortcut.full_clean()

    def test_shortcut_with_non_existing_category_fails(self):
        """Shortcut: fails to create with non existing 'category'"""
        non_existing_category = Category(user=self.user1, name="Food")
        shortcut = Shortcut(
            user = self.user1,
            name = "Tax",
            category = non_existing_category,
        )
        with self.assertRaisesMessage(ValidationError, "Category does not exists."):
            shortcut.full_clean()

    def test_shortcut_with_non_existing_fund_account_fails(self):
        """Shortcut: fails to create with non existing 'fund account'"""
        non_existing = FundAccount(user=self.user1, name="Wallet", balance=5000, currency=self.currency)
        shortcut = Shortcut(
            user = self.user1,
            name = "Tax",
            fund_account = non_existing
        )
        with self.assertRaisesMessage(ValidationError, "Fund Account does not exists."):
            shortcut.full_clean()

    # ------------ Selected non owned -----------------

    def test_shortcut_selected_category_is_not_owned_fails(self):
        """Shortcut: fails when selected 'category' is not owned by the 'user'"""
        category_user2 = Category.objects.create(user=self.user2, name="Travel")
        shortcut = Shortcut(
            user = self.user1,
            name = "Tax",
            category = category_user2
        )
        with self.assertRaisesMessage(ValidationError, "Category does not belongs to you."):
            shortcut.full_clean()

    def test_shortcut_selected_fund_account_is_not_owned_fails(self):
        """Shortcut: fails when selected 'fund account' is not owned by the 'user'"""
        fund_account_user2 = FundAccount.objects.create(user=self.user2, name="Wallet", currency=self.currency, balance=5000)
        shortcut = Shortcut(
            user = self.user1,
            name = "Tax",
            fund_account = fund_account_user2
        )
        with self.assertRaisesMessage(ValidationError, "Fund Account does not belongs to you."):
            shortcut.full_clean()

    # ---------- Uniqueness (case‑insensitive) ---------------
    
    def test_shortcut_duplicate_name_same_user_fails(self):
        """Shortcut: fails when duplicate 'name' exists for same 'user'"""
        Shortcut.objects.create(user=self.user1, name="Tax")
        duplicate = Shortcut(user=self.user1, name="tax")
        with self.assertRaisesMessage(ValidationError, f"Shortcut with Name: '{duplicate.name}' already exists."):
            duplicate.full_clean()

    def test_shortcut_duplicate_name_different_user_success(self):
        """Shortcut: succeeds when duplicate 'name' exists for different 'user'"""
        Shortcut.objects.create(user=self.user1, name="Tax")
        account = Shortcut(user=self.user2, name="Tax")
        account.full_clean()

    def test_shortcut_update_to_duplicate_name_same_user_fails(self):
        """Shortcut: fails when updating to duplicate 'name' for same 'user'"""
        shortcut1 = Shortcut.objects.create(user=self.user1, name="Tax")
        shortcut2 = Shortcut.objects.create(user=self.user1, name="Savings")
        shortcut2.name = "tax"
        with self.assertRaisesMessage(ValidationError, f"Shortcut with Name: '{shortcut2.name}' already exists."):
            shortcut2.full_clean()

    # ---------- Whitespace Normalization ----------

    def test_shortcut_whitespace_trimmed_success(self):
        """Shortcut: success to trim leading/trailing whitespace."""
        shortcut = Shortcut(user=self.user1, name="   Tax   ")
        shortcut.create_by(self.user1)
        self.assertEqual(shortcut.name, "Tax")

    def test_shortcut_name_with_whitespace_only_fails(self):
        """Shortcut: fails when 'name' is only whitespace"""
        shortcut = Shortcut(user=self.user1, name="   ")
        with self.assertRaisesMessage(ValidationError, "Name cannot be blank or whitespace."):
            shortcut.full_clean()

    # ------------ Amount rules ----------

    def test_shortcut_amount_negative_fails(self):
        """Shortcut: fails when 'amount' is negative"""
        shortcut = Shortcut(user=self.user1, name="Tax", amount=-100)
        with self.assertRaises(ValidationError):
            shortcut.full_clean()

    # ------------- Invalid choice -----------

    def test_shortcut_type_is_not_credit_or_debit_fails(self):
        """Shortcut: fails when 'type' is not 'credit' or 'debit'"""
        shortcut = Shortcut(user=self.user1, name="Tax", type = "invalid_type")
        with self.assertRaisesMessage(ValidationError, f"Value '{shortcut.type}' is not a valid choice."):
            shortcut.full_clean()

    # ----------- Character limit -------------

    def test_shortcut_name_exceeded_max_length_fails(self):
        """Shortcut: fails with exceeding max_length 'name'."""
        with self.assertRaises(ValidationError):
            shortcut = Shortcut(user=self.user1, name="x" * 121)
            shortcut.create_by(self.user1)

    # ----------- Valid owned data ----------------

    def test_shortcut_create_with_valid_values_success(self):
        """Shortcut: success to create with valid values"""
        shourtcut = Shortcut(user=self.user1, name="Tax", amount=100)
        shourtcut = shourtcut.create_by(self.user1)
        self.assertEqual(shourtcut.name, "Tax")
        self.assertEqual(shourtcut.user, self.user1)
        self.assertEqual(shourtcut.amount, 100)

    def test_shortcut_fetch_owned_success(self):
        """Shortcut: success to fetch owned fund shourtcut."""
        shortcut = Shortcut.objects.create(user=self.user1, name="Tax")
        fetched = Shortcut.get_for_user(self.user1, shortcut.pk)
        self.assertEqual(fetched.pk, shortcut.pk)

    def test_shortcut_update_owned_success(self):
        """Shortcut: success to update owned shortcut."""
        shortcut = Shortcut.objects.create(user=self.user1, name="Tax", amount=100)
        shortcut.amount = 5000
        shortcut.update_by(self.user1)
        self.assertEqual(shortcut.amount, 5000)

    # ----------- Others owned data ---------------

    def test_shortcut_fetch_others_owned_fails(self):
        """Shortcut: fail to fetch others owned shortcut."""
        shortcut = Shortcut.objects.create(user=self.user2, name="Tax")
        with self.assertRaisesMessage(PermissionDenied, "You are not the owner."):
            shortcut.get_for_user(self.user1, shortcut.pk)

    def test_shortcut_update_others_owned_fails(self):
        """Shortcut: fail to update others owned shortcut."""
        shortcut = Shortcut.objects.create(user=self.user2, name="Tax")
        shortcut.name = "Salary"
        with self.assertRaisesMessage(PermissionDenied, "You are not the owner."):
            shortcut.update_by(self.user1)

