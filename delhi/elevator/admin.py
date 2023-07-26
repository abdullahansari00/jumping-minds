from django.contrib import admin
from elevator import models


@admin.register(models.Elevator)
class ElevatorAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "current_floor", "up", "operational", "close")
    search_fields = ("id", "name")
    list_filter = ("current_floor", "operational")


@admin.register(models.ElevatorRequest)
class ElevatorRequestAdmin(admin.ModelAdmin):
    list_display = ("elevator_id", "from_floor", "to_floor")
    search_fields = ("elevator_id", "elevator__name")
