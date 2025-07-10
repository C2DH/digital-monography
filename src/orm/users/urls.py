from django.urls import path
from .views import dashboard, process, save_result

urlpatterns = [
    path("dashboard/", dashboard, name="dashboard"),
    path("process/", process, name="process_task"),
    path("save-result/", save_result, name="save_result"),
]
