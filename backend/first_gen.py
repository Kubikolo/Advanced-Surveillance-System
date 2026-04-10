import random
from input_validation import validate
from json_parser import parameters_parser
from path_generator import generate_paths_for_all_drones

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

if __name__ == '__main__':
    parameters = parameters_parser("../shared/parameters_base.json")
    objects = parameters["objects"]
    drones = parameters["drones"]
    waypoints = generate_first_gen(objects, drones)
    print(waypoints)
    print(generate_paths_for_all_drones(drones, waypoints))
    print(validate(time_ticks=100, width=60, height=60, objects=objects, drones=drones))