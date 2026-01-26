from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Category


@login_required(login_url='login')
def categories(request):
    categories_list = Category.get_for_user(requested_user=request.user)
    return render(request, 'category/index.html', {'categories_list': categories_list})

@login_required(login_url='login')
def create_category(request):
    try:
        context = {}
        if request.POST:
            category = Category(user=request.user, name=request.POST.get('name'))
            category = category.create_by(requested_user=request.user)
            messages.success(request, 'Category added successfully!!!')
    except ValidationError as ve:
        context['errors'] = ve
        print("VALIDATION ERROR:")
        print(ve)
        print("----------------------------")
    except Exception as e:
        messages.error(request, str(e))
        print("EXECPTION:")
        print(e)
        print("----------------------------")
    return render(request, 'category/form_create.html', context)

@login_required(login_url='login')
def update_category(request, id):
    try:
        context = {
            'category': Category.get_for_user(requested_user=request.user, id=id)
        }
        if request.POST:
            context['category'].name = request.POST.get('name')
            context['category'] = context['category'].update_by(requested_user=request.user)
            messages.success(request, 'Category updated successfully!!!')
    except ValidationError as ve:
        context['errors'] = ve
        print("VALIDATION ERROR:")
        print(ve)
        print("----------------------------")
    except Exception as e:
        messages.error(request, str(e))
        print("EXECPTION:")
        print(e)
        print("----------------------------")
    return render(request, 'category/form_update.html', context)