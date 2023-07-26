from django.db.models import Q
from django.utils import timezone
from django_celery_beat.models import IntervalSchedule, PeriodicTask
from elevator.models import Elevator, ElevatorRequest
from elevator.serializers import ElevatorSerializer
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class ElevatorViewSet(viewsets.ModelViewSet):
    serializer_class = ElevatorSerializer
    queryset = Elevator.objects.all()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def bulk_create_elevators(request, count):
    elevators = Elevator.objects.bulk_create([Elevator() for x in range(count)])
    serializer = ElevatorSerializer(elevators, many=True)

    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def request_elevator(request):
    if not Elevator.objects.filter(operational=True).exists():
        return Response("No elevators available!")

    operational_elevators = Elevator.objects.filter(operational=True)

    from_floor = int(request.data.get("from_floor"))
    to_floor = int(request.data.get("to_floor"))

    if from_floor == to_floor:
        return Response("Same floor!")
    elif from_floor < Elevator.MIN_FLOOR or to_floor > Elevator.MAX_FLOOR:
        return Response("Provided floor does not exists")

    up_elevator = (
        operational_elevators.filter(
            Q(Q(up__isnull=True) | Q(up=True)), current_floor__lt=from_floor
        )
        .order_by("-current_floor")
        .first()
    )

    down_elevator = (
        operational_elevators.filter(
            Q(Q(up__isnull=True) | Q(up=False)), current_floor__gt=from_floor
        )
        .order_by("current_floor")
        .first()
    )

    if not up_elevator and not down_elevator:
        if abs(from_floor - Elevator.MIN_FLOOR) < abs(from_floor - Elevator.MAX_FLOOR):
            elevator = (
                operational_elevators.filter(
                    Q(Q(up__isnull=True) | Q(up=False)), current_floor__lt=from_floor
                )
                .order_by("current_floor")
                .first()
            )
        else:
            elevator = (
                operational_elevators.filter(
                    Q(Q(up__isnull=True) | Q(up=True)), current_floor__gt=from_floor
                )
                .order_by("-current_floor")
                .first()
            )
    else:
        if not up_elevator:
            elevator = down_elevator
        elif not down_elevator:
            elevator = up_elevator
        else:
            if abs(from_floor - up_elevator.current_floor) < abs(
                from_floor - down_elevator.current_floor
            ):
                elevator = up_elevator
            else:
                elevator = down_elevator

    elevator.traverse_floors.append(from_floor)
    elevator.save()

    ElevatorRequest.objects.update_or_create(
        elevator=elevator,
        from_floor=from_floor,
        to_floor=to_floor,
    )
    print(elevator.id)

    if (
        elevator.close
        and not PeriodicTask.objects.filter(
            name=f"ElevatorMoveNext{elevator.id}", one_off=False
        ).exists()
    ):
        PeriodicTask.objects.update_or_create(
            name=f"ElevatorMoveNext{elevator.id}",
            defaults={
                "interval": IntervalSchedule.objects.get_or_create(
                    every=Elevator.ELEVATOR_TIME, period=IntervalSchedule.SECONDS
                )[0],
                "task": "elevator_move_next",
                "args": [elevator.id],
                "description": elevator.id,
                "one_off": True,
                "enabled": True,
                "start_time": timezone.now() + timezone.timedelta(seconds=Elevator.ELEVATOR_TIME),
            },
        )

    return Response("Request placed!")
