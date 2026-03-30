import random
from drone import Drone
from input_validation import validate

def generate_first_gen(objects, drones):

    first_gen = []

    for _ in drones:
        waypoints = []
        random.shuffle(objects)
        for object in objects:
            random_cell = random.choice(object)
            waypoints.append(random_cell)
        first_gen.append(waypoints)

    return first_gen

if __name__ == '__main__':

    objects = [
        [(3,3),(3,4),(3,5),(3,6),(3,7),
         (4,3),(4,4),(4,5),(4,6),(4,7),
         (5,3),(5,4),(5,5),(5,6),(5,7),
         (6,3),(6,4),(6,5),(6,6),(6,7),
         (7,3),(7,4),(7,5),(7,6),(7,7)],

        [(20,10),(21,10),(22,10),(23,10),(24,10),
         (20,11),(20,12),(20,13),(20,14)],

        [(40,5),(41,5),(42,5),(43,5),
         (40,6),(41,6),(42,6),(43,6),
         (40,7),(41,7),(42,7),(43,7),
         (40,8),(41,8),(42,8),(43,8),
         (40,9),(41,9),(42,9),(43,9),
         (40,10),(41,10),(42,10),(43,10)],

        [(30,40),(31,40),(32,40),
         (30,41),(31,41),(32,41),(33,41),
         (29,42),(30,42),(31,42),(32,42),
         (30,43),(31,43),(32,43),
         (31,44)]
    ]


    drones = [
        Drone((5,50), tickspeed=2, radius=5),
        Drone((50,50), tickspeed=3, radius=6),
        Drone((25,25), tickspeed=2, radius=4)
    ]


    print(generate_first_gen(objects, drones))
    print(validate(time_ticks=100, width=60, height=60, objects=objects, drones=drones))