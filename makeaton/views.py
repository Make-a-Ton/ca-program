from django.shortcuts import render, redirect
from config.settings import ADMIN_URL


# Create your views here.

def index(request):
    return redirect(ADMIN_URL)
