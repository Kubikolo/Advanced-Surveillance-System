import json
import sys

from first_gen import generate_first_gen
from drone import Drone
from path_generator import generate_path, generate_paths_for_all_drones


def drone_serializer(obj):
    if isinstance(obj, Drone):
        return {
            "starting_position": obj.starting_position,
            "radius": obj.radius,
            "tickspeed": obj.tickspeed
        }
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def parameters_parser(filename):
    with open(filename) as json_file:
        parameters = json.load(json_file)
    objects = [[(x, y) for x, y in inner] for inner in parameters["objects"]]
    drones = [Drone((drone["starting_position"][0], drone["starting_position"][1]), drone["tickspeed"], drone["radius"]) for drone in parameters["drones"]]
    dimensions = (parameters["dimensions"][0], parameters["dimensions"][1])
    return {"objects":objects, "drones":drones, "dimensions":dimensions}

def simulation_json_generator(filename, initial_steps, loop_steps, parameters):
    with open(filename, 'w') as json_file:
        json.dump({
                    "initial_steps": initial_steps,
                    "loop_steps": loop_steps,
                    "objects": parameters["objects"],
                    "drones": parameters["drones"],
                    "dimensions": parameters["dimensions"]
                    }, json_file,
                    default=drone_serializer,
                    indent=4)

    return

if __name__ == "__main__":
    filename = sys.argv[1]
    parameters = parameters_parser(f"../shared/parameters_{filename}.json")
    waypoints = generate_first_gen(parameters["objects"], parameters["drones"])
    print(waypoints)
    result = generate_paths_for_all_drones(parameters["drones"], waypoints)
    simulation_json_generator(f"../shared/simulation_{filename}.json", result[0], result[1], parameters)
