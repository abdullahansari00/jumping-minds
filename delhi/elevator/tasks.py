from ast import literal_eval

from django.utils import timezone
from django_celery_beat.models import IntervalSchedule, PeriodicTask
from elevator.models import Elevator, ElevatorRequest

from delhi.celery import app


@app.task(name="elevator_move_next")
def elevator_move_next(elevator_id):
    elevator = Elevator.objects.get(id=elevator_id)
    elevator.current_floor = elevator.next_floor
    elevator.save()

    if elevator.current_floor in elevator.traverse_floors:
        elevator.close = False
        elevator_requests = ElevatorRequest.objects.filter(
            elevator=elevator, from_floor=elevator.current_floor
        )
        requested_floors = list(elevator_requests.values_list("to_floor", flat=True))
        elevator.traverse_floors.extend(requested_floors)
        elevator.traverse_floors.remove(elevator.current_floor)
        elevator.save()
        elevator_requests.delete()

        PeriodicTask.objects.update_or_create(
            name=f"ElevatorDoorOpen{elevator_id}",
            defaults={
                "interval": IntervalSchedule.objects.get_or_create(
                    every=Elevator.ELEVATOR_TIME, period=IntervalSchedule.SECONDS
                )[0],
                "task": "elevator_door_open",
                "args": [elevator_id],
                "description": elevator_id,
                "one_off": True,
                "enabled": True,
                "start_time": timezone.now() + timezone.timedelta(seconds=Elevator.ELEVATOR_TIME),
            },
        )

    elif elevator.traverse_floors:
        task = PeriodicTask.objects.filter(name=f"ElevatorMoveNext{elevator_id}").first()
        task.enabled = True
        task.start_time = None
        task.save()


@app.task(name="elevator_door_open")
def elevator_door_open(elevator_id):
    elevator = Elevator.objects.get(id=elevator_id)
    elevator.close = True
    elevator.save()

    if elevator.traverse_floors:
        task = PeriodicTask.objects.get(name=f"ElevatorMoveNext{elevator_id}")
        task.enabled = True
        task.start_time = timezone.now() + timezone.timedelta(seconds=Elevator.ELEVATOR_TIME)
        task.save()


@app.task(name="continue_elevator_move")
def continue_elevator_move():
    use_elevators = Elevator.objects.filter(up__isnull=False).values_list("id", flat=True)
    open_door_elevators = PeriodicTask.objects.filter(
        task="elevator_door_open", enabled=True
    ).values_list("description", flat=True)
    tasks = PeriodicTask.objects.filter(
        task="elevator_move_next",
        description__in=use_elevators,
    ).exclude(description__in=open_door_elevators)

    for task in tasks:
        app.send_task("elevator_move_next", literal_eval(task.args))
