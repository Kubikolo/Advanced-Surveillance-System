def check_positions_boundary(cell, width, height):
    return 0 <= cell[0] < width and 0 <= cell[1] < height


def check_orthogonal(object):
    visited = set()

    def dfs(cell):
        if cell in visited: return
        if cell not in object: return
        visited.add(cell)
        for direction in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            new_cell = cell[0] + direction[0], cell[1] + direction[1]
            dfs(new_cell)
        return

    dfs(object[0])

    return len(visited) == len(object)



def validate(time_ticks, width, height, objects, drones):
    if time_ticks <= 0: return False
    if width <= 0: return False
    if height <= 0: return False
    if len(objects) == 0: return False
    if len(drones) == 0: return False

    for i, object in enumerate(objects):
        for j, cell in enumerate(object):
            if not check_positions_boundary(cell, width, height): return False
        if not check_orthogonal(object): return False

    for i, drone in enumerate(drones):
        if not check_positions_boundary(drone.starting_position, width, height): return False
        if drone.tickspeed < 1: return False
        if drone.radius < 0: return False

    return True

if __name__ == "__main__":
    objects = [
        [(3, 3), (3, 4), (3, 5), (3, 6), (3, 7),
         (4, 3), (4, 4), (4, 5), (4, 6), (4, 7),
         (5, 3), (5, 4), (9, 5), (5, 6), (5, 7),
         (6, 3), (6, 4), (6, 5), (6, 6), (6, 7),
         (7, 3), (7, 4), (7, 5), (7, 6), (7, 7)],

        [(19, 10), (21, 10), (22, 10), (23, 10), (24, 10),
         (20, 11), (20, 12), (20, 13), (20, 14)],

        [(40, 5), (41, 5), (42, 5), (43, 5),
         (40, 6), (41, 6), (42, 6), (43, 6),
         (40, 7), (41, 7), (42, 7), (43, 7),
         (40, 8), (41, 8), (42, 8), (43, 8),
         (40, 9), (41, 9), (42, 9), (43, 9),
         (40, 10), (41, 10), (42, 10), (43, 10)],

        [(30, 40), (31, 40), (32, 40),
         (30, 41), (31, 41), (32, 41), (33, 41),
         (29, 42), (30, 42), (31, 42), (32, 42),
         (30, 43), (31, 43), (32, 43),
         (31, 44)]
    ]

    for object in objects:
        # false, false, true, true
        print(check_orthogonal(object))

