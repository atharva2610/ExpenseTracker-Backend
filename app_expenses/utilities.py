import io
import csv
from .models import Currency, FundAccount, Category, Tag
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

def email_exists(email):
    return get_user_model().objects.filter(email=email).exists()

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
    
def is_valid_for_report(month, year):
    if not month.isnumeric() or not year.isnumeric() or int(month) < 1 or int(month) > 12 or int(year) < 2000 or int(year) > 3000:
        return False
    return True

def monthly_report_csv(filtered_trx_list):
    csv_report_columns = ['id', 'amount', 'type', 'date', 'currency', 'fund_account_id', 'fund_account_name', 'category_id', 'category_name', 'description', 'tags']
    buffer = io.StringIO()
    if len(filtered_trx_list) > 0:
        data = []
        for trx in filtered_trx_list:
            data_row = [trx.id, trx.amount, trx.type, trx.date, trx.fund_account.currency.id, trx.fund_account.id, trx.fund_account.name,
                trx.category.id, trx.category.name, trx.description]
            data.append(data_row)
        writer = csv.writer(buffer, csv_report_columns)
        writer.writerow(csv_report_columns)
        writer.writerows(data)
    return buffer.getvalue()