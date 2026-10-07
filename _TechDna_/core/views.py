import logging
from django.shortcuts import render

logger = logging.getLogger(__name__)

def home(request):
    logger.info("Home view rendered")
    return render(request, "core/home.html")