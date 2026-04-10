import json

from backend.path_generator import generate_path


def parameters_parser(filename):
    with open(filename) as json_file:
        parameters = json.load(json_file)
    return parameters

def simulation_json_generator(filename, initial_steps, loop_steps, parameters):
    with open(f"../shared/{filename}", 'w') as json_file:
        json.dump({
                    "initial_steps": initial_steps,
                    "loop_steps": loop_steps,
                    "objects": parameters["objects"],
                    "drones": parameters["drones"],
                    "dimensions": parameters["dimensions"]
                    }, json_file)

    return

if __name__ == "__main__":
    waypoints = [(20, 11), (31, 41), (40, 10), (3, 7)]
    starting_position = (0, 0)
    result = generate_path(starting_position, waypoints)
    simulation_json_generator("simulation_base.json", result[0], result[1], parameters_parser("../shared/parameters_base.json"))
