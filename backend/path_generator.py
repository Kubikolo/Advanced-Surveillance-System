from bresenham import bresenham

def generate_paths_for_all_drones(drones, gen):
    first_paths = []
    cycles = []
    for drone, waypoints in zip(drones, gen):
        first_segment, rest = generate_path(drone.starting_position, waypoints)
        first_paths.append(first_segment)
        cycles.append(rest)
    return first_paths, cycles

def generate_path(starting_position, waypoints):
    first_segment = list(bresenham(starting_position[0], starting_position[1], waypoints[0][0], waypoints[0][1]))[:-1]
    rest = []
    for first_point, second_point in zip(waypoints[:-1], waypoints[1:]):
        rest.extend(list(bresenham(first_point[0], first_point[1], second_point[0], second_point[1])))

    rest.extend(list(bresenham(waypoints[-1][0], waypoints[-1][1], waypoints[0][0], waypoints[0][1]))[:-1])

    return first_segment, rest

if __name__ == '__main__':
    waypoints = [(20, 11), (31, 41), (40, 10), (3, 7)]
    starting_position = (0, 0)
    print(generate_path(starting_position, waypoints))