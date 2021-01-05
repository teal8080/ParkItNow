import threading
import time

import pyrebase

import firebase_admin
from firebase_admin import messaging
from firebase_admin import credentials
from firebase_admin import firestore
from google.api_core.datetime_helpers import DatetimeWithNanoseconds
import datetime

config = {
    'apiKey': "AIzaSyBd_NC2WenOrpS-J9xWXoQf9-hBcP843Ko",
    'authDomain': "parkitnow-a8dc8.firebaseapp.com",
    'databaseURL': "https://parkitnow-a8dc8.firebaseio.com",
    'projectId': "parkitnow-a8dc8",
    'storageBucket': "parkitnow-a8dc8.appspot.com",
    'messagingSenderId': "296134061159",
    'appId': "1:296134061159:web:b3873f1989c5e4633038c2"
}

cred = credentials.Certificate("key.json")
default_app = firebase_admin.initialize_app(cred)

db = firestore.client()


def send_notifications(title, body, tokens):
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        tokens=tokens
    )
    response = messaging.send_multicast(message)
    print('{0} messages were sent successfully'.format(response.success_count))


def send_notification(title, body, token):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token
    )
    response = messaging.send(message)
    print("Successfully sent message:", response)


# users_ref = db.collection(u'users')
# docs = users_ref.stream()
#
# for doc in docs:
#     print(f'{doc.id} => {doc.to_dict()}')

callback_done = threading.Event()

first_time = True
cars = {}


def get_blocked_cars(car_id_changed):
    blocked_cars = []

    current_car_ids = [car_id_changed]
    while current_car_ids:
        current_blocking = []
        for current_car_id in current_car_ids:
            blocking = cars[current_car_id]['blocking']
            for blocker_car_id in blocking:
                if blocker_car_id not in current_blocking:
                    current_blocking.append(blocker_car_id)
        current_car_ids = current_blocking
        blocked_cars.extend(current_blocking)

    return list(set(blocked_cars))


def unobstructed(current_car_id):
    global cars
    for car, data in cars.items():
        if data['blocking'] == current_car_id:
            return True
    return False


def last_element_is_root(path):
    return not cars[path[len(path) - 1]]['blocking']


def last_element_is_user_car(path, car_id):
    return path[len(path) - 1] == car_id


def found_all_paths(paths, car_id):
    for path in paths:
        if not last_element_is_user_car(path, car_id) and not last_element_is_root(path):
            return False
    return True


def grow_path(path, car_id):
    new_paths = []

    if last_element_is_root(path) or last_element_is_user_car(path, car_id):
        new_paths.append(path)
        return new_paths

    blocked_cars = cars[path[len(path) - 1]]['blocking']

    for j in range(len(blocked_cars)):
        new_path = []
        new_path.extend(path)
        new_path.append(blocked_cars[j])
        new_paths.append(new_path)

    return new_paths


def get_blockers_of(car_id_changed):
    global cars
    paths = []

    blocked_cars = []
    for _, data in cars.items():
        blocked_cars.append(data['blocking'])
    flat_blocked_cars = [item for sublist in blocked_cars for item in sublist]
    blocked_cars = list(set(flat_blocked_cars))

    unobstructed_cars = []
    for car_id in cars:
        if car_id not in blocked_cars:
            unobstructed_cars.append(car_id)

    for car_id in unobstructed_cars:
        paths.append([])
        paths[len(paths) - 1].append(car_id)

    while not found_all_paths(paths, car_id_changed):
        new_paths = []
        for i in range(len(paths)):
            new_paths.extend(grow_path(paths[i], car_id_changed))
        paths = new_paths

    new_paths = []
    for path in paths:
        if car_id_changed in path:
            new_paths.append(path)
    paths = new_paths

    blocked_by_user = get_blocked_cars(car_id_changed)

    blockers = []
    for car in list(set([item for sublist in paths for item in sublist])):
        if car not in blocked_by_user and not car == car_id_changed:
            blockers.append(car)

    return blockers


def notify_blockers(blockers, car_id_changed):
    tokens = []
    for blocker in blockers:
        print("BLOCKER:", blocker)
        doc = db.collection(u"users").where(u'selectedCar', u'==', blocker).get()
        if len(doc) > 0:
            # send_notification("ParkItNow",
            #                   car_id_changed + " is leaving NOW!",
            #                   doc[0]._data['token'])
            tokens.append(doc[0]._data['token'])

    send_notifications("ParkItNow",
                       car_id_changed + " is leaving NOW!",
                       tokens)


def on_snapshot(doc_snapshot, changes, read_time):
    global first_time, cars

    if first_time:
        first_time = False
        for doc in doc_snapshot:
            cars.update({doc.id: doc._data})
    else:
        for change in changes:
            print(f'Changed document snapshot: {change.document.id}')

            if change.type.name == 'ADDED':
                # there's either a new user, or a user changed his car (both unparked)
                cars.update({change.document.id, change.document._data})

            elif change.type.name == 'REMOVED':
                cars.pop(change.document.id, None)

            elif change.type.name == 'MODIFIED':
                # either somebody parked, or somebody changed the time when he leaves, ~or somebody left~(cut this one
                # out cause we just leave the old data in there)
                #
                # other potential cases: leaveable/blocked_user_left_announcer was switched.
                #
                # I don't know if the following is relevant anymore:
                #  I'll need some flags (synchronous) in order to tackle the case when time is changed and it's gonna be
                #  treated in the while loop too
                #
                if change.document.id not in cars:
                    # somebody just added a new car
                    cars.update({change.document.id, change.document._data})
                else:
                    # sb changed the time when he leaves:
                    leave_time: DatetimeWithNanoseconds = change.document._data['departureTime']
                    if abs(cars[change.document.id]['departureTime'] - leave_time) > datetime.timedelta(seconds=1):
                        # 1) sb leaves now
                        now = DatetimeWithNanoseconds.now(tz=datetime.timezone.utc)
                        if abs(leave_time - now) < datetime.timedelta(minutes=1):
                            blockers = get_blockers_of(change.document.id)
                            notify_blockers(blockers, change.document.id)
                        # 2) sb leaves later
                        #   don't care
                        # 3) sb leaves sooner
                        #   don't care

    callback_done.set()


cars_ref = db.collection(u'cars')

cars_ref.on_snapshot(on_snapshot)

while True:
    # continuously check how much time is left until car leaves
    pass

# send_notification("Hello",
#                   "Python salutes you",
#                   "ecKGGi8rTJeorv1uXAyowp:APA91bECrBQyfgs9QyeqWUiohtDY1wDhiK8LuxGFatokUZITscvK7QDPZTPBSbRpbluXeRtNXL3LgvxffPV2J6HFt1Agkv8wpi1Vq7eEwVsoS9JCISVZ96yBtWnXJW_Dn6RGrr5B17jQ")
