from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models


class Elevator(models.Model):
    # Time taken by elevator to move from one floor to consecutive next floor
    ELEVATOR_TIME = 5
    MIN_FLOOR = -2
    MAX_FLOOR = 8

    name = models.CharField(max_length=256, null=True, blank=True)
    current_floor = models.IntegerField(default=0)
    traverse_floors = ArrayField(models.IntegerField(), default=list, blank=True)
    close = models.BooleanField(default=True)
    up = models.BooleanField(null=True)
    operational = models.BooleanField(default=True)

    class Meta:
        db_table = "elevator"
        verbose_name = "Elevator"
        verbose_name_plural = "Elevators"

    def __str__(self):
        return str(self.id)

    def clean(self):
        if self.traverse_floors and (
            min(self.traverse_floors) < self.MIN_FLOOR or max(self.traverse_floors) > self.MAX_FLOOR
        ):
            raise ValidationError('"Traverse floors" contains floors which does not exist')

    def save(self, *args, **kwargs):
        self.clean()
        self.traverse_floors = list(set(self.traverse_floors))
        # rdb.set_trace()

        if self.traverse_floors:
            if self.up == True and (
                ((self.next_floor) > self.MAX_FLOOR) or (self.current_floor > self.next_floor)
            ):
                self.up = False
            elif self.up == False and (
                ((self.next_floor) < self.MIN_FLOOR) or (self.current_floor < self.next_floor)
            ):
                self.up = True
            elif self.up == None and self.current_floor < self.next_floor:
                self.up = True
            elif self.up == None and self.current_floor > self.next_floor:
                self.up = False
            elif not self.traverse_floors:
                self.up = None
        else:
            self.up = None

        super().save(*args, **kwargs)

    @property
    def next_floor(self):
        if self.traverse_floors:
            if self.up == True and max(self.traverse_floors) > self.current_floor:
                return self.current_floor + 1
            elif self.up == True and max(self.traverse_floors) < self.current_floor:
                return self.current_floor - 1
            elif self.up == False and min(self.traverse_floors) < self.current_floor:
                return self.current_floor - 1
            elif self.up == False and min(self.traverse_floors) > self.current_floor:
                return self.current_floor + 1
            else:
                return self.traverse_floors[0]
        return self.current_floor

    @property
    def time_to_next_floor(self):
        return abs(self.current_floor - self.next_floor) * self.ELEVATOR_TIME


class ElevatorRequest(models.Model):
    elevator = models.ForeignKey(Elevator, on_delete=models.CASCADE)
    from_floor = models.IntegerField()
    to_floor = models.IntegerField()

    class Meta:
        db_table = "elevator_request"
        verbose_name = "ElevatorRequest"
        verbose_name_plural = "Elevator Requests"

    def __str__(self):
        return f"{self.elevator.id}: {self.from_floor}-{self.to_floor}"
