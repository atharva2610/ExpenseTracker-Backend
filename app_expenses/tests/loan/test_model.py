from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, PermissionDenied
from app_expenses.models import Loan, Currency
from datetime import date

User = get_user_model()

class LoanModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(username="user1")
        self.user2 = User.objects.create(username="user2")
        self.currency = Currency.objects.create(id="INR", symbol="₹", name="Indian Rupee")

    # ---------- Missing field ------------

    def test_loan_with_missing_user_fails(self):
        """Loan: fails when 'user' is missing"""
        loan = Loan(
            from_entity = "Bank",
            currency = self.currency,
            amount = 1000,
            remaining_amount = 200,
            interest_rate = 10
        )
        with self.assertRaisesMessage(ValidationError, "User does not exists."):
                loan.full_clean()

    def test_loan_with_missing_from_entity_fails(self):
        """Loan: fails when 'from_entity' is missing"""
        loan = Loan(
            user = self.user1,
            currency = self.currency,
            amount = 1000,
            remaining_amount = 200,
            interest_rate = 10
        )
        with self.assertRaisesMessage(ValidationError, "From entity is required."):
                loan.full_clean()

    def test_loan_with_missing_currency_fails(self):
        """Loan: fails when 'currency' is missing"""
        loan = Loan(
            user = self.user1,
            from_entity = "Bank",
            amount = 1000,
            remaining_amount = 200,
            interest_rate = 10
        )
        with self.assertRaisesMessage(ValidationError, "Currency does not exists."):
                loan.full_clean()
    
    def test_loan_with_missing_amount_fails(self):
        """Loan: fails when 'amount' is missing"""
        loan = Loan(
            user = self.user1,
            from_entity = "Bank",
            currency = self.currency,
            remaining_amount = 200,
            interest_rate = 10
        )
        with self.assertRaisesMessage(ValidationError, "Amount is required."):
                loan.full_clean()
    
    def test_loan_with_missing_remaining_amount_success(self):
        """Loan: success to set default zero when 'remaining amount' is missing"""
        loan = Loan(
            user = self.user1,
            from_entity = "Bank",
            currency = self.currency,
            amount = 1000,
            interest_rate = 10
        )
        loan.full_clean()
        self.assertEqual(loan.remaining_amount, 0)
    
    def test_loan_with_missing_interest_rate_success(self):
        """Loan: success to set default zero when 'interest rate' is missing"""
        loan = Loan(
            user = self.user1,
            from_entity = "Bank",
            currency = self.currency,
            amount = 1000,
            remaining_amount = 200
        )
        loan.full_clean()
        self.assertEqual(loan.interest_rate, 0)

    # ---------- Non existing User/Currency --------------

    def test_loan_with_non_existing_user_fails(self):
        """Loan: fails with non existing 'user'"""
        non_existing_user = User(username="not-exists")
        loan = Loan(
            user = non_existing_user,
            from_entity = "Bank",
            currency = self.currency,
            amount = 1000
        )
        with self.assertRaises(ValidationError):
            loan.full_clean()
    
    def test_loan_with_non_existing_currency_fails(self):
        """Loan: fails with non existing 'currency'"""
        non_existing_currency = Currency(id="hash", symbol="#", name="Hash")
        loan = Loan(
            user = self.user1,
            from_entity = "Bank",
            amount = 1000,
            currency = non_existing_currency
        )
        with self.assertRaises(ValidationError):
            loan.full_clean()

    # ---------- Whitespace normalization ----------

    def test_loan_whitespace_trimmed_success(self):
        """Loan: success to trim leading/trailing whitespace."""
        loan = Loan(
            user = self.user1,
            from_entity = "  Bank  ",
            currency = self.currency,
            amount = 150000
        )
        loan.create_by(self.user1)
        self.assertEqual(loan.from_entity, "Bank")

    def test_loan_from_entity_with_whitespace_only_fails(self):
        """Loan: fails or normalizes when 'from entity' is only whitespace"""
        loan = Loan(
            user = self.user1,
            from_entity = "   ",
            currency = self.currency,
            amount = 150000
        )
        with self.assertRaisesMessage(ValidationError, "From entity cannot be blank or whitespace."):
            loan.full_clean()

    # ---------- Amount / Remaining amount / Interest rules ---------
    
    def test_loan_amount_zero_or_negative_fails(self):
        """Loan: fails when amount <= 0"""
        for val in [0, -100]:
            loan = Loan(
                user = self.user1,
                from_entity = "Bank",
                currency = self.currency,
                amount = val
            )
            with self.assertRaises(ValidationError):
                loan.full_clean()

    def test_loan_remaining_amount_negative_fails(self):
        """Loan: fails when remaining < 0"""
        loan = Loan(
                user = self.user1,
                from_entity = "Bank",
                currency = self.currency,
                amount = 1000,
                remaining_amount = -100
            )
        with self.assertRaises(ValidationError):
            loan.full_clean()
        
    def test_remaining_amount_morethan_loan_amount_fails(self):
        """Loan: fails when remaining amount > loan amount"""
        loan = Loan(
                user = self.user1,
                from_entity = "Bank",
                currency = self.currency,
                amount = 1000,
                remaining_amount = 2000
            )
        with self.assertRaisesMessage(ValidationError, "Remaining amount cannot be more than loan amount."):
            loan.full_clean()

    def test_loan_completed_autoset_remaining_amount_zero_success(self):
        """Loan: success to set 'remaining amount' zero when 'completed'."""
        loan = Loan.objects.create(
                user = self.user1,
                from_entity = "Bank",
                currency = self.currency,
                amount = 1000,
                remaining_amount = 100
            )
        loan.completed = True
        loan = loan.update_by(self.user1)
        self.assertTrue(loan.completed)
        self.assertEqual(loan.remaining_amount, 0)

    def test_loan_remaining_amount_zero_autoset_completed_success(self):
        """Loan: success to set 'completed' True when 'remaining amount' is zero."""
        loan = Loan.objects.create(
                user = self.user1,
                from_entity = "Bank",
                currency = self.currency,
                amount = 1000,
                remaining_amount = 100
            )
        self.assertFalse(loan.completed)
        loan.completed = True
        loan.update_by(self.user1)
        self.assertEqual(loan.remaining_amount, 0)
        self.assertTrue(loan.completed)
        
    def test_loan_interest_rate_not_in_range_fails(self):
        """Loan: fails when 'interest rate' is not in range (0 to 100)"""
        for interest_rate in [-5, 150]:
            loan = Loan(
                user = self.user1,
                from_entity = "Bank",
                currency = self.currency,
                amount = 1000,
                interest_rate = interest_rate
            )
            with self.assertRaises(ValidationError):
                loan.full_clean()

    # ------------ Invalid choice -------------

    def test_loan_type_is_not_borrowed_or_lended_fails(self):
        """Loan: fails when type is not 'borrowed' or 'lended'"""
        trx = Loan(
                user=self.user1,
                currency = self.currency,
                type = "invlaid",
                from_entity="Bank",
                amount=1000
            )
        with self.assertRaisesMessage(ValidationError, f"Value '{trx.type}' is not a valid choice."):
            trx.full_clean()

    # ----------- Date range ------------

    def test_loan_date_in_valid_range_success(self):
        """Loan: success when date is b/w 2000-01-01 and today"""
        for loan_date in [date(2000,1,1), date.today()]:
            loan = Loan(
                user = self.user1,
                currency = self.currency,
                from_entity = "Bank",
                amount = 1000,
                date = loan_date
            )
            loan = loan.create_by(self.user1)
            self.assertIn(loan.date, [date(2000, 1, 1), date.today()])

    def test_loan_date_outoff_range_fails(self):
        """Loan: fails when date is before 2000-01-01 or after today"""
        for loan_date in [date(1999,1,1), date(2100,1,1)]:
            loan = Loan(
                user=self.user1,
                currency = self.currency,
                from_entity="Bank",
                amount=1000,
                date=loan_date
            )
            with self.assertRaises(ValidationError):
                loan.full_clean()

    def test_loan_due_date_is_not_after_date_fails(self):
        """Loan: fails when due date > loan date"""
        loan = Loan(
                user=self.user1,
                currency = self.currency,
                from_entity="Bank",
                amount=1000,
                date = date(2025, month=11, day=14),
                due_date = date(year=2025, month=10, day=26)
            )
        with self.assertRaisesMessage(ValidationError, "Due date must come after loan date."):
            loan.full_clean()

        # ----------- Character limit -------------

    # ----------- Character limit -------------

    def test_loan_from_entity_exceeded_max_length_fails(self):
        """Loan: fails with exceeding max_length 'from entity'."""
        with self.assertRaises(ValidationError):
            loan = Loan(
                user = self.user1,
                currency = self.currency,
                from_entity = "X"*121,
                amount = 1000
            )
            loan.create_by(self.user1)

    # ----------- Valid owned data ----------------

    def test_loan_create_with_valid_values_success(self):
        """Loan: success to create with valid values"""
        loan = Loan(
            user = self.user1,
            currency = self.currency,
            from_entity = "Bank",
            amount = 1000
        )
        loan = loan.create_by(self.user1)
        self.assertEqual(loan.from_entity, "Bank")
        self.assertEqual(loan.user, self.user1)
        self.assertEqual(loan.currency, self.currency)
        self.assertEqual(loan.amount, 1000)

    def test_loan_fetch_owned_success(self):
        """Loan: success to fetch owned loan."""
        loan = Loan.objects.create(
            user = self.user1,
            currency = self.currency,
            from_entity = "Bank",
            amount = 1000
        )
        fetched = Loan.get_for_user(self.user1, loan.pk)
        self.assertEqual(fetched.pk, loan.pk)

    def test_loan_update_owned_success(self):
        """Loan: success to update owned loan."""
        loan = Loan.objects.create(
            user = self.user1,
            currency = self.currency,
            from_entity = "Bank",
            amount = 1000
        )
        loan.amount = 5000
        loan = loan.update_by(self.user1)
        self.assertEqual(loan.amount, 5000)

    # ----------- Others owned data ---------------

    def test_loan_fetch_others_owned_fails(self):
        """Loan: fail to fetch others owned loan."""
        loan = Loan.objects.create(
            user = self.user2,
            currency = self.currency,
            from_entity = "Bank",
            amount = 1000
        )
        with self.assertRaisesMessage(PermissionDenied, "You are not the owner."):
            Loan.get_for_user(self.user1, loan.pk)

    def test_loan_update_others_owned_fails(self):
        """Loan: fail to update others owned loan."""
        loan = Loan.objects.create(
            user = self.user2,
            currency = self.currency,
            from_entity = "Bank",
            amount = 1000
        )
        loan.amount = 5000
        with self.assertRaisesMessage(PermissionDenied, "You are not the owner."):
            loan.update_by(self.user1)

