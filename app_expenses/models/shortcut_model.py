import uuid
from django.db import models
from django.db.models.functions import Lower
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from .owned_model import OwnedModel
from .category_model import Category
from .fund_account_model import FundAccount
from .tag_model import Tag
from .transaction_model import TransactionType

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