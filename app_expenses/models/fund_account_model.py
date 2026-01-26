import uuid
from django.db import models
from django.db.models.functions import Lower
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from .owned_model import OwnedModel
from .currency_model import Currency

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
        return self.name