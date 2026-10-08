import logging
from django.contrib import messages
from django.shortcuts import redirect, render
from .forms import RegisterForm, ProfileForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__ )




def register_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")    
    
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            logger.info("Nuevo candidato/evaluador registrado en Tech DNA: %s", user.username)
            messages.success(request, f"¡Bienvenido a Tech DNA, {user.first_name or user.username}! Tu cuenta ha sido creada.")


            return redirect("core:home")

    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    return render(request, "accounts/profile.html")

@login_required
def profile_edit(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)

        if form.is_valid():
            user = form.save()
            messages.success(request, "Perfil técnico actualizado correctamente.")
            return redirect("accounts:profile")

    else:
        form = ProfileForm(instance=request.user)

    return render(request, "accounts/profile_edit.html", {"form": form})
    
