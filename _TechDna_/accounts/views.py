from django.shortcuts import redirect, render
from django.http import HttpResponse
from .forms import RegisterForm
from django.contrib.auth import login, logout


def login_view(request):
    return HttpResponse("Página de login en construcción")


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            return redirect("core:home")

    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("core:home")