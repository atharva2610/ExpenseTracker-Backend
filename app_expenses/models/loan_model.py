import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from .owned_model import OwnedModel
from .currency_model import Currency
from ..custom_validators import today, validate_date

    
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