import uuid
import calendar
from typing import *
from datetime import date
from django.db import models
from django.db.models.functions import Lower, Now, ExtractYear
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from .custom_wrappers import balance_updater

def today():
    return timezone.now().date()

def validate_year(value):
    if value < 2000 or value > timezone.datetime.now().year:
        raise ValidationError("Year cannot be less than 2000 or in future.")
    
def validate_date(value):
    if value and (value > timezone.datetime.now().date()):
        raise ValidationError("Date cannot be in future.")
    validate_oldest_date(value)
    
def validate_oldest_date(value):
    if value and value < date(year=2000, month=1, day=1):
        raise ValidationError("Date cannot be older than '2000-01-01'")

class OwnedModel(models.Model):
    """
    Mixin for models that are owned by a User. Provides small helpers to assert
    ownership and perform save/update/create operations that validate owner at runtime.
    """
    owner_field_name = 'user'

    class Meta:
        abstract = True

    @property
    def owner(self) -> User|None:
        return getattr(self, self.owner_field_name, None)

    def is_owned_by(self, user: User|None) -> bool:
        return self.owner is not None and user is not None and self.owner == user
    
    def assert_owned_by(self, requested_user: User | None):
        if requested_user is None:
            raise PermissionDenied("Requested User must be provided.")
        if self.owner is None:
            raise PermissionDenied("Data is predefined and not owned.")
        if self.owner != requested_user:
            raise PermissionDenied("You are not the owner.")
        
    def _clean_string_value(self):
        for field in self._meta.fields:
            value = getattr(self, field.name)
            if isinstance(value, str):
                value = value.strip()
                if value == "":
                    # normalize empty strings to None if field allows blank
                    if getattr(field, "blank", False) and getattr(field, "null", False):
                        value = None
            setattr(self, field.name, value)
    
    def save_obj(self) -> Any:
        self._clean_string_value()
        self.full_clean()
        self.save()
        return self

    def create_by(self, requested_user: User) -> Any:
        if not self._state.adding: # self._state.adding == True → object is not yet saved (new instance).
            raise PermissionDenied("You cannot use this method to update data.")
        self.assert_owned_by(requested_user)
        if self.owner is None:
            setattr(self, self.owner_field_name, requested_user)
        return self.save_obj()
    
    def update_by(self, requested_user: User) -> Any:
        if self._state.adding: # self._state.adding == False → object is already saved in DB.
            raise PermissionDenied("You cannot use this method to create data.")
        self.assert_owned_by(requested_user)
        obj = self.__class__.objects.get(pk=self.pk)
        obj_owner = getattr(obj, self.owner_field_name)
        # Only the owner can update
        if obj_owner != requested_user:
            raise PermissionDenied("No permission to perform this action.")
        return self.save_obj()
    
    def delete_by(self, requested_user: User) -> Any:
        if self._state.adding: # self._state.adding == False → object is already saved in DB.
            raise PermissionDenied("Data does not exists.")
        self.assert_owned_by(requested_user)
        obj = self.__class__.objects.get(pk=self.pk)
        obj_owner = getattr(obj, self.owner_field_name)
        # Only the owner can delete
        if obj_owner != requested_user:
            raise PermissionDenied("No permission to perform this action.")
        return self.delete()
    
    @classmethod
    def get_for_user(cls, requested_user=None, id=None):
        if id is None:
            raise PermissionDenied("ID is required.")
        if requested_user is None:
            raise PermissionDenied("Requested User must be provided.")
        obj = cls.objects.get(id=id)
        if obj.owner is not None and obj.owner != requested_user:
            raise PermissionDenied("You are not the owner.")
        return obj


class Currency(models.Model):
    id = models.CharField(primary_key=True, max_length=4)
    symbol = models.CharField(max_length=8)
    name = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower('name'),
                Lower('symbol'),
                name='unique_currency_name_symbol_ci'
            )
        ]
    
    def clean(self):
        super().clean()
        # validate id
        if not self.id:
            raise ValidationError({"id": "ID is required."})
        if not self.id.strip():
            raise ValidationError({"id": "ID cannot be blank or whitespace."})
        # validate symbol
        if not self.symbol:
            raise ValidationError({"symbol": "Symbol is required."})
        if not self.symbol.strip():
            raise ValidationError({"symbol": "Symbol cannot be blank or whitespace."})
        # validate name
        if not self.name:
            raise ValidationError({"name": "Name is required."})
        if not self.name.strip():
            raise ValidationError({"name": "Name cannot be blank or whitespace."})
        # validate uniqueness
        if Currency.objects.filter(symbol__iexact=self.symbol.strip()).exclude(pk=self.pk).exists():
            raise ValidationError({"symbol": f"Currency with Symbol: '{self.symbol}' already exists."})
        if Currency.objects.filter(name__iexact=self.name.strip()).exclude(pk=self.pk).exists():
            raise ValidationError({"symbol": f"Currency with Name: '{self.name}' already exists."})
    
    def save(self, *args, **kwargs):
        self.id = self.id.strip().upper()
        self.symbol = self.symbol.strip()
        self.name = self.name.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.id


class FundAccount(OwnedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fund_accounts')
    name = models.CharField(max_length=120)
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower('name'), 'user', name='unique_fund_account_per_user'),
        ]

    def clean(self):
        super().clean()
        # validate user
        if not self.user_id:
            raise ValidationError({"user": "User does not exists."})
        # validate name
        if not self.name:
            raise ValidationError({"name": "Name is required."})
        if not self.name.strip():
            raise ValidationError({"name": "Name cannot be blank or whitespace."})
        # validate currency
        if not self.currency_id:
            raise ValidationError({"currency": "Currency does not exists."})
        # validate uniqueness
        if FundAccount.objects.filter(user=self.user, name__iexact=self.name.strip()).exclude(pk=self.pk).exists():
            raise ValidationError({"name": f"Fund account with Name: '{self.name}' already exists."})        
    
    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.id


class Category(OwnedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=120)

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower('name'), 'user', name='unique_category_per_user'),
        ]
    
    def clean(self):
        super().clean()
        # validate user
        if not self.user_id:
            raise ValidationError({"user": "User does not exists."})
        # validate name
        if not self.name:
            raise ValidationError({"name": "Name is required."})
        if not self.name.strip():
            raise ValidationError({"name": "Name cannot be blank or whitespace."})
        # validate uniqueness
        if Category.objects.filter(user=None, name__iexact=self.name.strip()).exclude(pk=self.pk).exists():
            raise ValidationError({"name": f"Predefined category with Name: '{self.name}' already exists."})
        if Category.objects.filter(user=self.user, name__iexact=self.name.strip()).exclude(pk=self.pk).exists():
            raise ValidationError({"name": f"Category with Name: '{self.name}' already exists."})        

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Tag(OwnedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='tags')

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower('name'), 'user', name='unique_tag_per_user'),
        ]

    def clean(self):
        super().clean()
        # validate user
        if not self.user_id:
            raise ValidationError({"user": "User does not exists."})
        # validate name
        if not self.name:
            raise ValidationError({"name": "Name is required."})
        if not self.name.strip():
            raise ValidationError({"name": "Name cannot be blank or whitespace."})
        # validate uniqueness
        if Tag.objects.filter(user=self.user, name__iexact=self.name.strip()).exclude(pk=self.pk).exists():
            raise ValidationError({"name": f"Tag with Name: '{self.name}' already exists."})        

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class TransactionType(models.TextChoices):
        DEBIT = 'debit', 'Debit'
        CREDIT = 'credit', 'Credit'

class Transaction(OwnedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='transactions')
    amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0.01)])
    fund_account = models.ForeignKey(FundAccount, null=True, blank=True, on_delete=models.SET_NULL, related_name='transactions')
    tags = models.ManyToManyField(Tag, blank=True, related_name='transactions')
    date = models.DateField(default=today, db_index=True, validators=[validate_date])
    type = models.CharField(max_length=6, choices=TransactionType.choices, default=TransactionType.DEBIT)
    description = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name='transaction_amount_positive'),
            models.CheckConstraint(condition=models.Q(type__in=[TransactionType.CREDIT, TransactionType.DEBIT]), name='valid_transaction_type')
        ]
        ordering = ['-date']
    
    def clean(self):
        super().clean()
        # validate user
        if not self.user_id:
            raise ValidationError({"user": "User does not exists."})
        # validate category
        if not self.category_id or not Category.objects.filter(pk=self.category.pk).exists():
            raise ValidationError({"Category": "Category does not exists."})
        if self.category and self.category.user != self.user:
            raise ValidationError({"category": "Category does not belongs to you."})
        # validate amount
        if not self.amount:
            raise ValidationError({"amount": "Amount is required."})
       # validate fund account
        if not self.fund_account_id or not FundAccount.objects.filter(pk=self.fund_account.pk).exists():
            raise ValidationError({"fund_account": "Fund Account does not exists."})
        if self.fund_account and self.fund_account.user != self.user:
            raise ValidationError({"fund_account": "Fund Account does not belongs to you."})
        
    @balance_updater
    def save(self, *args, **kwargs):
        if self.description:
            self.description = self.description.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.id}"

class Shortcut(OwnedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shortcuts')
    name = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    type = models.CharField(max_length=6, choices=TransactionType.choices, default=TransactionType.DEBIT)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='shortcuts')
    fund_account = models.ForeignKey(FundAccount, null=True, blank=True, on_delete=models.SET_NULL, related_name='shortcuts')
    tags = models.ManyToManyField(Tag, blank=True, related_name='shortcuts')

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower('name'),'user', name='unique_shortcut_per_user'),
            models.CheckConstraint(condition=models.Q(amount__gte=0), name='positive_amount'),
            models.CheckConstraint(condition=models.Q(type__in=[TransactionType.CREDIT, TransactionType.DEBIT]), name='valid_shortcut_transaction_type')
        ]
    
    def clean(self):
        super().clean()
        # validate user
        if not self.user_id:
            raise ValidationError({"user": "User does not exists."})
        # validate name
        if not self.name:
            raise ValidationError({"name": "Name is required."})
        if not self.name.strip():
            raise ValidationError({"name": "Name cannot be blank or whitespace."})
        # validate category
        if self.category_id and not Category.objects.filter(pk=self.category.pk).exists():
            raise ValidationError({"Category": "Category does not exists."})
        if self.category and self.category.user != self.user:
            raise ValidationError({"category": "Category does not belongs to you."})
        # validate fund account
        if self.fund_account_id and not FundAccount.objects.filter(pk=self.fund_account.pk).exists():
            raise ValidationError({"fund_account": "Fund Account does not exists."})
        if self.fund_account and self.fund_account.user != self.user:
            raise ValidationError({"fund_account": "Fund Account does not belongs to you."})
        # validate uniqueness
        if Shortcut.objects.filter(user=self.user, name__iexact=self.name.strip()).exclude(pk=self.pk).exists():
            raise ValidationError({"name": f"Shortcut with Name: '{self.name}' already exists."})
        
    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user} - {self.name}"

class Report(OwnedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    year = models.PositiveSmallIntegerField(validators=[validate_year], db_index=True)
    month = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)], db_index=True)
    total_debit = models.DecimalField(max_digits=16, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_credit = models.DecimalField(max_digits=16, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    is_dirty = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'year', 'month'], name='unique_report_per_user_month'),
            models.CheckConstraint(condition=models.Q(month__gt=0) & models.Q(month__lte=12), name='valid_month'),
            models.CheckConstraint(condition=models.Q(total_debit__gte=0), name='postive_total_debit'),
            models.CheckConstraint(condition=models.Q(total_credit__gte=0), name='positive_total_credit'),
        ]
    
    @property
    def net_balance(self):
        return self.total_credit - self.total_debit
    
    @property
    def month_year(self):
        return f"{calendar.month_name[self.month]} {self.year}"
    
    def clean(self):
        super().clean()
        # validate user
        if not self.user_id:
            raise ValidationError({"user": "User does not exists."})
        # validate year
        if not self.year:
            raise ValidationError({"year": "Year is required."})
        # if self.year < 2000:
        #     raise ValidationError({"year": "Year must be >= 2000."})
        # if self.year > today().year:
        #     raise ValidationError({"year": "Year cannot be in the future."})
        # validate month
        if not self.month:
            raise ValidationError({"month": "Month is required."})
        # validate uniqueness
        if Report.objects.filter(user=self.user, year=self.year, month=self.month).exclude(pk=self.pk).exists():
            raise ValidationError({"month_year": f"Report with Month Year: '{self.month_year}' already exists."})

    def __str__(self):
        return f"{self.user} - {self.month_year}"
    
class LoanType(models.TextChoices):
    BORROWED = 'borrowed', 'Borrowed'
    LENDED   = 'lended', 'Lended'

class Loan(OwnedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    type = models.CharField(max_length=10, choices=LoanType.choices, default=LoanType.BORROWED)
    from_entity = models.CharField(max_length=120)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, null=True, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0.01)])
    remaining_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    completed = models.BooleanField(default=False)
    date = models.DateField(default=today, db_index=True, validators=[validate_date])
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    due_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        constraints = [
            models.CheckConstraint(condition=models.Q(type__in=[LoanType.BORROWED, LoanType.LENDED]), name="valid_loan_type"),
            models.CheckConstraint(condition=models.Q(amount__gt=0), name='positive_loan_amount'),
            models.CheckConstraint(condition=models.Q(remaining_amount__gte=0), name='positive_remaining_amount'),
            models.CheckConstraint(condition=models.Q(interest_rate__gte=0), name='positive_interest_rate'),
        ]
        indexes = [models.Index(fields=['user', 'completed'])]
    
    @property
    def total_payable(self):
        return self.amount + (self.amount * (self.interest_rate / 100))

    def clean(self):
        super().clean()
        # validate user
        if not self.user_id:
            raise ValidationError({"user": "User does not exists."})
        # validate from entity
        if not self.from_entity:
            raise ValidationError({"from_entity": "From entity is required."})
        if not self.from_entity.strip():
            raise ValidationError({"from_entity": "From entity cannot be blank or whitespace."})
        # validate currency
        if not self.currency_id:
            raise ValidationError({"currency": "Currency does not exists."})
        # validate amount
        if not self.amount:
            raise ValidationError({"amount": "Amount is required."})
        # validate remaining amount
        if self.remaining_amount > self.amount:
            raise ValidationError({"remaining_amount": "Remaining amount cannot be more than loan amount."})
        # validate due date
        if self.due_date and self.due_date < self.date:
            raise ValidationError({"due_date": "Due date must come after loan date."})

    def save(self, *args, **kwargs):
        self.from_entity = self.from_entity.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.type} - {self.from_entity}"