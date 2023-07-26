from django.urls import path
from elevator.views import bulk_create_elevators, request_elevator

urlpatterns = [
    path("bulk-create-elevators/<int:count>/", bulk_create_elevators, name="bulk_create_elevators"),
    path("request-elevator/", request_elevator, name="request_elevator"),
]
