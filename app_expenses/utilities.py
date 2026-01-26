from .models import Currency, FundAccount, Category, Tag
from django.core.exceptions import ValidationError

def get_currency_list():
    return Currency.objects.all()

def get_currency_by_id(id):
    try:
        return Currency.objects.get(id=id)
    except Currency.DoesNotExist:
        raise ValidationError({'currency': 'Currency ID: {id} is invalid!'})
    except Exception as e:
        raise ValidationError({'currency': str(e)})

def get_fund_account_list():
    return FundAccount.objects.all()

def get_fund_account_by_id(id):
    try:
        return FundAccount.objects.get(id=id)
    except FundAccount.DoesNotExist:
        raise ValidationError({'fund_account': 'Fund Account ID: {id} is invalid!'})
    except Exception as e:
        raise ValidationError({'fund_account': e})

def get_category_list():
    return Category.objects.all()

def get_category_by_id(id):
    try:
        return Category.objects.get(id=id)
    except Category.DoesNotExist:
        raise ValidationError({'category': 'Category ID: {id} is invalid!'})
    except Exception as e:
        raise ValidationError({'category': e})

def get_tag_list():
    return Tag.objects.all()

def get_tag_by_id(id):
    try:
        return Tag.objects.get(id=id)
    except Tag.DoesNotExist:
        raise ValidationError({'tag': 'Tag ID: {id} is invalid!'})
    except Exception as e:
        raise ValidationError({'tag': e})