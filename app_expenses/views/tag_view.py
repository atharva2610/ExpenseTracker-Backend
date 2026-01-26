from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Tag


@login_required(login_url='login')
def tags(request):
    tags_list = Tag.get_for_user(requested_user=request.user)
    return render(request, 'Tag/index.html', {'tags_list': tags_list})

@login_required(login_url='login')
def create_tag(request):
    try:
        context = {}
        if request.POST:
            tag = Tag(user=request.user, name=request.POST.get('name'))
            tag = tag.create_by(requested_user=request.user)
            messages.success(request, 'Tag added successfully!!!')
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
    return render(request, 'tag/form_create.html', context)

@login_required(login_url='login')
def update_tag(request, id):
    try:
        context = {
            'tag': Tag.get_for_user(requested_user=request.user, id=id)
        }
        if request.POST:
            context['tag'].name = request.POST.get('name')
            context['tag'] = context['tag'].update_by(requested_user=request.user)
            messages.success(request, 'Tag updated successfully!!!')
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
    return render(request, 'tag/form_update.html', context)