from django.shortcuts import render
from django.http import JsonResponse
import requests


# def dashboard(request):
#     print(type(request))
#     return render(request, "dashboard.html")


def process(request):
    print("process")
    print(type(request))
    return JsonResponse({"status": "success"})


def save_result(request):
    print("save_result")
    print(type(request))
    print("Task completed! Time to save the data to our database.")
    return JsonResponse({"status": "success"})
