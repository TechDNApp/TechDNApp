from django.shortcuts import render


def home(request):
    context = {
        "platform_name": "Tech DNA",
        "academy": "Ducky Academy",
    }
    return render(request, "core/home.html", context)
