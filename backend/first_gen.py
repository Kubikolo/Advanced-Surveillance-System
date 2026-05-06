import random

def generate_first_gen(objects, drones):

    first_gen = []

    for _ in drones:
        waypoints = []
        random.shuffle(objects)
        random_objects_subset = random.sample(objects, random.randint(2, len(objects)))
        for object in random_objects_subset:
            random_cell = random.choice(object)
            waypoints.append(random_cell)
        first_gen.append(waypoints)

    return first_gen
