from django.test import TestCase
from app_expenses.models import FundAccount, Currency
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, PermissionDenied

User = get_user_model()

class FundAccountModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(username="user1")
        self.user2 = User.objects.create(username="user2")
        self.currency = Currency.objects.create(id="INR", symbol="₹", name="Indian Rupee")

    # ------------ Missing field ---------------

    def test_fund_acct_missing_user_fails(self):
        """FundAccount: fails when 'user' is missing"""
        account = FundAccount(name="Wallet", balance=100, currency=self.currency)
        with self.assertRaisesMessage(ValidationError, "User does not exists."):
            account.full_clean()

    def test_fund_acct_missing_name_fails(self):
        """FundAccount: fails when 'name' is missing"""
        account = FundAccount(user=self.user1, balance=100, currency=self.currency)
        with self.assertRaisesMessage(ValidationError, "Name is required."):
            account.full_clean()

    def test_fund_acct_missing_balance_fails(self):
        """FundAccount: success to set default zero when 'balance' is missing"""
        account = FundAccount(user=self.user1, name="Wallet", currency=self.currency)
        account.full_clean()
        self.assertEqual(account.balance, 0)

    def test_fund_acct_missing_currency_fails(self):
        """FundAccount: fails when 'currency' is missing"""
        account = FundAccount(user=self.user1, name="Wallet", balance=100)
        with self.assertRaisesMessage(ValidationError, "Currency does not exists."):
            account.full_clean()

    # ---------- Non existing User/Currency --------------

    def test_fund_acct_create_with_non_existing_user_fails(self):
        """FundAccount: fails to create with non existing 'user'"""
        non_existing_user = User(username="not-exists")
        account = FundAccount(user=non_existing_user, name="Wallet", balance=100, currency=self.currency)
        with self.assertRaises(ValidationError):
            account.full_clean()
    
    def test_fund_acct_create_with_non_existing_currency_fails(self):
        """FundAccount: fails to create with non existing 'currency'"""
        non_existing_currency = Currency(id="hash", symbol="#", name="Hash")
        account = FundAccount(user=self.user1, name="Wallet", balance=100, currency=non_existing_currency)
        with self.assertRaises(ValidationError):
            account.full_clean()

    # ---------- Uniqueness (case‑insensitive) ---------------
    
    def test_fund_acct_duplicate_name_same_user_fails(self):
        """FundAccount: fails when duplicate 'name' (case-insensitive) exists for same user"""
        FundAccount.objects.create(user=self.user1, name="Wallet", balance=100, currency=self.currency)
        duplicate = FundAccount(user=self.user1, name="wallet", balance=200, currency=self.currency)
        with self.assertRaisesMessage(ValidationError, f"Fund account with Name: '{duplicate.name}' already exists."):
            duplicate.full_clean()

    def test_fund_acct_duplicate_name_different_users_success(self):
        """FundAccount: succeeds when duplicate 'name' exists for different users"""
        FundAccount.objects.create(user=self.user1, name="Wallet", balance=100, currency=self.currency)
        account = FundAccount(user=self.user2, name="Wallet", balance=200, currency=self.currency)
        account.full_clean()

    def test_fund_acct_update_to_duplicate_name_same_user_fails(self):
        """FundAccount: fails when updating to duplicate 'name' for same user"""
        acc1 = FundAccount.objects.create(user=self.user1, name="Wallet", balance=100, currency=self.currency)
        acc2 = FundAccount.objects.create(user=self.user1, name="Savings", balance=200, currency=self.currency)
        acc2.name = "wallet"
        with self.assertRaisesMessage(ValidationError, f"Fund account with Name: '{acc2.name}' already exists."):
            acc2.full_clean()

    # ------------ Balance rules --------------

    def test_fund_acct_balance_negative_fails(self):
        """FundAccount: fails when 'balance' is negative"""
        account = FundAccount(user=self.user1, name="Wallet", balance=-100, currency=self.currency)
        with self.assertRaises(ValidationError):
            account.full_clean()

    # ---------- Whitespace Normalization ----------

    def test_fund_acct_whitespace_trimmed_success(self):
        """FundAccount: success to trim leading/trailing whitespace."""
        fund_account = FundAccount(user=self.user1, name="   Wallet   ", balance=1000, currency=self.currency)
        fund_account.create_by(self.user1)
        self.assertEqual(fund_account.name, "Wallet")

    def test_fund_acct_name_with_whitespace_only_fails(self):
        """FundAccount: fails when 'name' is only whitespace"""
        account = FundAccount(user=self.user1, name="   ", balance=100, currency=self.currency)
        with self.assertRaisesMessage(ValidationError, "Name cannot be blank or whitespace."):
            account.full_clean()

    # ----------- Character limit -------------

    def test_fund_acct_name_exceeded_max_length_fails(self):
        """FundAccount: fails with exceeding max_length 'name'."""
        with self.assertRaises(ValidationError):
            fund_account = FundAccount(user=self.user1, name="x" * 121, balance=1000, currency=self.currency)
            fund_account.create_by(self.user1)

    # ----------- Valid owned data ----------------

    def test_fund_acct_create_with_valid_values_success(self):
        """FundAccount: success to create with valid 'user', 'name', 'balance', 'currency'"""
        account = FundAccount(user=self.user1, name="Wallet", balance=100, currency=self.currency)
        account = account.create_by(self.user1)
        self.assertEqual(account.name, "Wallet")
        self.assertEqual(account.user, self.user1)
        self.assertEqual(account.currency, self.currency)

    def test_fund_acct_fetch_owned_success(self):
        """FundAccount: success to fetch owned fund account."""
        fund_account = FundAccount.objects.create(user=self.user1, name="HDFC Bank", balance=2000, currency=self.currency)
        fetched = FundAccount.get_for_user(self.user1, fund_account.pk)
        self.assertEqual(fetched.pk, fund_account.pk)

    def test_fund_acct_update_owned_success(self):
        """FundAccount: success to update owned fund account."""
        fund_account = FundAccount.objects.create(user=self.user1, name="HDFC Bank", balance=2000, currency=self.currency)
        fund_account.balance = 5000
        fund_account.update_by(self.user1)
        self.assertEqual(fund_account.balance, 5000)

    # ----------- Others owned data ---------------

    def test_fund_account_fetch_others_owned_fails(self):
        """Fund Account: fail to fetch others owned fund account."""
        fund_account = FundAccount.objects.create(user=self.user2, balance=1000, currency=self.currency, name="Wallet")
        with self.assertRaisesMessage(PermissionDenied, "You are not the owner."):
            fund_account.get_for_user(self.user1, fund_account.pk)

    def test_fund_account_update_others_owned_fails(self):
        """Fund Account: fail to update others owned fund account."""
        fund_account = FundAccount.objects.create(user=self.user2, name="Wallet", balance=1000, currency=self.currency)
        fund_account.name = "Bank"
        with self.assertRaisesMessage(PermissionDenied, "You are not the owner."):
            fund_account.update_by(self.user1)

