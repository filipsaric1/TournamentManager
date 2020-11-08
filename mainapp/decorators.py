from django.shortcuts import redirect
from .models import User
from django.http import HttpResponse
def creator_required(function):
    def wrap(request, *args, **kwargs):
        if request.user.role == User.Role.CREATOR:
            return function(request, *args, **kwargs)
        else:
            return redirect('401')
    return wrap

def admin_required(function):
    def wrap(request, *args, **kwargs):
        if request.user.role == User.Role.ADMIN:
            return function(request, *args, **kwargs)
        else:
            return redirect('401')
    return wrap
