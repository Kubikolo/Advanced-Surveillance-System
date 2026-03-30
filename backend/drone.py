from dataclasses import dataclass

@dataclass
class Drone:
    starting_position: tuple
    tickspeed: int
    radius: int