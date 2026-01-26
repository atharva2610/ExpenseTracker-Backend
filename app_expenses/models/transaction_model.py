import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from ..custom_wrappers import balance_updater
from .owned_model import OwnedModel
from .category_model import Category
from .fund_account_model import FundAccount
from .tag_model import Tag
from ..custom_validators import today, validate_date


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
        return f"{self.user} - {self.date}"