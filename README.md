## Elevator System

The Elevator System is a Django-based application that manages a simplified elevator model. It allows you to create 'n' elevators, call an elevator and get you to your desired floor. It performs operations such as moving up/down, opening/closing doors, and marking elevators as not working or in maintenance.

### Setup

1. Create and activate a virtual environment.
```
python -m venv venv
source venv/bin/activate
```
2. Download the requirements given in the `requirements.txt` file.
```
pip install -r requirements.txt
```
3. Apply migrations.
```
python manage.py migrate
```
4. Run the development server.
```
python manage.py runserver
```
5. Run celery tasks
```
celery -A delhi beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
celery -A delhi worker -l info
```

### API Endpoints

1. Initialize the elevator system:
    - **Description**: Creates "n" number of elevators.
    - **Method**: POST
    - **Endpoint**: `/elevator/bulk-create-elevators/<elevator_count>/`
2. Request an elevator:
    - **Description**: When this API is called, an elevator near to your floor is selected in an optimized manner. After reaching to your floor, the door is opened and then closed. Then the elevator takes you to your desired floor. It also makes stops if required by other passengers. After reahing to your desired floor, again the door is opened and then closed
    - **Method**: POST
    - **Endpoint**: `/elevator/request-elevator/`
    - **Form data**:
        - from_floor
        - to_floor
3. ViewSets:
    - **Description**: 
        1. This will show you list of elevators.
        2. Here you can also view details of the elevator like:
            - requests
            - next destination
            - if the elevator is moving up/down currently
            - if the door is open/close
            - if the elevator is working
        3. You can also mark the elevator as working or not.
    - **Endpoints**:
        1. `/view-sets/elevator/`
        2. `/view-sets/elevator/<elevator_id>/`
