from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'index.html')

def home(request):
    return render(request, 'base.html')

def about(request):
    return render(request, 'base.html')  # TODO
