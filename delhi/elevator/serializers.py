from elevator.models import Elevator
from rest_framework import serializers


class ElevatorSerializer(serializers.ModelSerializer):
    next_floor = serializers.SerializerMethodField()

    class Meta:
        model = Elevator
        fields = "__all__"

    def get_next_floor(self, elevator):
        return elevator.next_floor
