from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from app_expenses.models import Transaction, FundAccount, Category, Currency, TransactionType
from datetime import date

User = get_user_model()

class TransactionModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(username="user1")
        self.user2 = User.objects.create(username="user2")
        self.category = Category.objects.create(user=self.user1, name="Food")
        self.currency = Currency.objects.create(id="INR", symbol="₹", name="Indian Rupee")
        self.fund_account = FundAccount.objects.create(user=self.user1, name="Bank", currency=self.currency, balance=5000)
    
    # ----------- Missing field---------------

    def test_transaction_with_missing_user_fails(self):
        """Transaction: fails when user is missing"""
        trx = Transaction(
            category = self.category,
            amount = 100,
            fund_account = self.fund_account
        )
        with self.assertRaisesMessage(ValidationError, "User does not exists."):
            trx.full_clean()

    def test_transaction_with_missing_category_fails(self):
        """Transaction: fails when category is missing"""
        trx = Transaction(
            user = self.user1,
            amount = 100,
            fund_account = self.fund_account
        )
        with self.assertRaisesMessage(ValidationError, "Category does not exists."):
            trx.full_clean()

    def test_transaction_with_missing_fund_account_fails(self):
        """Transaction: fails when fund account is missing"""
        trx = Transaction(
            user = self.user1,
            category = self.category,
            amount = 100
        )
        with self.assertRaisesMessage(ValidationError, "Fund Account does not exists."):
            trx.full_clean()

    def test_transaction_with_missing_amount_fails(self):
        """Transaction: fails when amount is missing"""
        trx = Transaction(
            user=self.user1,
            category = self.category,
            fund_account = self.fund_account
        )
        with self.assertRaisesMessage(ValidationError, "Amount is required."):
            trx.full_clean()

    # ---------- Non existing User/Category/Fund Account --------------

    def test_transaction_with_non_existing_user_fails(self):
        """Transaction: fails to create with non existing 'user'"""
        non_existing_user = User(username="new_user")
        trx = Transaction(
            user = non_existing_user,
            category = self.category,
            amount = 100,
            fund_account = self.fund_account
        )
        with self.assertRaisesMessage(ValidationError, "User does not exists."):
            trx.full_clean()

    def test_transaction_with_non_existing_category_fails(self):
        """Transaction: fails to create with non existing 'category'"""
        non_existing = Category(user=self.user1, name="Food")
        trx = Transaction(
            user = self.user1,
            category = non_existing,
            amount = 100,
            fund_account = self.fund_account
        )
        with self.assertRaisesMessage(ValidationError, "Category does not exists."):
            trx.full_clean()

    def test_transaction_with_non_existing_fund_account_fails(self):
        """Transaction: fails to create with non existing 'fund account'"""
        non_existing = FundAccount(user=self.user1, name="Wallet")
        trx = Transaction(
            user = self.user1,
            category = self.category,
            amount = 100,
            fund_account = non_existing
        )
        with self.assertRaisesMessage(ValidationError, "Fund Account does not exists."):
            trx.full_clean()

    # ------------ Selected non owned -----------------

    def test_transaction_selected_category_is_not_owned_fails(self):
        """Transaction: fails when selected category is not owned by the user"""
        category_user2 = Category.objects.create(user=self.user2, name="Travel")
        trx = Transaction(
            user=self.user1,
            category = category_user2,
            amount = 100,
            fund_account = self.fund_account
        )
        with self.assertRaisesMessage(ValidationError, "Category does not belongs to you."):
            trx.full_clean()

    def test_transaction_selected_fund_account_is_not_owned_fails(self):
        """Transaction: fails when selected fund account is not owned by the user"""
        fund_account_user2 = FundAccount.objects.create(user=self.user2, name="Wallet", currency=self.currency)
        trx = Transaction(
            user=self.user1,
            category = self.category,
            amount = 100,
            fund_account = fund_account_user2
        )
        with self.assertRaisesMessage(ValidationError, "Fund Account does not belongs to you."):
            trx.full_clean()

    # ------------ Amount rules ----------

    def test_transaction_amount_zero_or_negative_fails(self):
        """Transaction: fails when amount is zero or negative"""
        for val in [0, -100]:
            trx = Transaction(
                user=self.user1,
                category = self.category,
                fund_account = self.fund_account,
                amount = val
            )
            with self.assertRaises(ValidationError):
                trx.full_clean()

    # ------------- Invalid choice -----------

    def test_transaction_type_is_not_credit_or_debit_fails(self):
        """Transaction: fails when type is not 'credit' or 'debit'"""
        trx = Transaction(
            user=self.user1,
            category = self.category,
            amount = 100,
            fund_account = self.fund_account,
            type = "invalid_type"
        )
        with self.assertRaisesMessage(ValidationError, f"Value '{trx.type}' is not a valid choice."):
            trx.full_clean()
   
    # ------------- Date range -------------

    def test_transaction_date_in_valid_range_success(self):
        """Transaction: success when date is b/w 2000-01-01 and today"""
        for trx_date in [date(2000,1,1), date.today()]:
            trx = Transaction(
                user=self.user1,
                category = self.category,
                amount = 100,
                fund_account = self.fund_account,
                date = trx_date
            )
            trx = trx.create_by(self.user1)
            self.assertIn(trx.date, [date(2000, 1, 1), date.today()])

    def test_transaction_date_outoff_range_fails(self):
        """Transaction: fails when date is before 2000-01-01 or after today"""
        for trx_date in [date(1999,1,1), date(2100,1,1)]:
            trx = Transaction(
                user=self.user1,
                category = self.category,
                amount = 100,
                fund_account = self.fund_account,
                date = trx_date
            )
            with self.assertRaises(ValidationError):
                trx.full_clean()

    # ------------- Verify fund balance on transaction create/update --------------

    def test_transaction_create_updates_balance(self):
        """Transaction: Verify that creating a transaction correctly updates the associated fund account balance. """
        initial_fund_balance = self.fund_account.balance
        trx = Transaction(
                user=self.user1,
                category = self.category,
                amount = 100,
                fund_account = self.fund_account,
                type = TransactionType.DEBIT
            )
        self.assertEqual(trx.amount, 100)
        # balance before transaction
        self.assertEqual(self.fund_account.balance, initial_fund_balance)
        trx = trx.create_by(self.user1)
        # balance after transaction
        self.assertEqual(self.fund_account.balance, initial_fund_balance - trx.amount)

    def test_transaction_update_changes_fund_account_balance(self):
        """
            Transaction: Verify that updating a transaction to a different fund account reverts the old account balance
            and applies the new account balance.
        """
        # Initial Balance
        fund_acct_one_balance = self.fund_account.balance
        trx = Transaction.objects.create(
                user=self.user1,
                category = self.category,
                amount = 500,
                fund_account = self.fund_account,
                type = TransactionType.DEBIT
            )
        self.assertEqual(trx.amount, 500)
        # fund account one balance after create transaction
        self.assertEqual(self.fund_account.balance, fund_acct_one_balance - trx.amount)
        
        fund_acct_two = FundAccount.objects.create(user=self.user1, name="Wallet", balance=1000, currency=self.currency)
        fund_acct_two_balance = fund_acct_two.balance
        # update transaction, change fund account
        trx.fund_account = fund_acct_two
        trx = trx.update_by(self.user1)
        # Refresh fund account
        self.fund_account.refresh_from_db()
        # fund account one balance, should have reverted transaction amount
        self.assertEqual(self.fund_account.balance, fund_acct_one_balance)
        # fund account two balance, should have updated transaction amount
        self.assertEqual(fund_acct_two.balance, fund_acct_two_balance - trx.amount)

    def test_transaction_update_amount_same_fund_account(self):
        """
        Verify that updating a transaction amount under the same fund account
        reverts the old amount and applies the new amount correctly.
        """
        # Initial balance
        initial_balance = self.fund_account.balance

        # Create transaction
        trx = Transaction.objects.create(
            user=self.user1,
            category=self.category,
            amount=200,
            fund_account=self.fund_account,
            type=TransactionType.DEBIT
        )
        self.assertEqual(self.fund_account.balance, initial_balance - 200)

        # Update transaction amount under same fund account
        trx.amount = 500
        trx = trx.update_by(self.user1)

        # Refresh fund account
        self.fund_account.refresh_from_db()

        # Balance should revert old amount (200) and apply new amount (500)
        expected_balance = initial_balance - 500
        self.assertEqual(self.fund_account.balance, expected_balance)

    def test_transaction_update_type_same_fund_account(self):
        """
        Verify that updating a transaction type (debit → credit or credit → debit)
        under the same fund account reverts the old type's balance effect and applies the new one.
        """
        # Initial balance
        initial_balance = self.fund_account.balance

        # Create a debit transaction
        trx = Transaction.objects.create(
            user=self.user1,
            category=self.category,
            amount=300,
            fund_account=self.fund_account,
            type=TransactionType.DEBIT
        )
        self.assertEqual(self.fund_account.balance, initial_balance - 300)

        # Update transaction type to credit (same fund account)
        trx.type = TransactionType.CREDIT
        trx = trx.update_by(self.user1)

        # Refresh fund account
        self.fund_account.refresh_from_db()

        # Balance should revert old debit (-300) and apply new credit (+300)
        expected_balance = initial_balance + 300
        self.assertEqual(self.fund_account.balance, expected_balance)


