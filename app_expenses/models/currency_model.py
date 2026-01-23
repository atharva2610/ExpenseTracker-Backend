from django.db import models
from django.db.models.functions import Lower
from django.core.exceptions import ValidationError

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