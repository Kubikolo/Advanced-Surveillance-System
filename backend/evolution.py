from first_gen import generate_first_gen
from path_generator import generate_paths_for_all_drones
from json_parser import parameters_parser, simulation_json_generator
import random
import sys
import copy

class Evolution:
    def __init__(self, parameters, total_generations):
        self.population = []
        self.generation_number = 0

        self.parameters = parameters
        self.drones = parameters['drones']
        self.objects = parameters['objects']
        self.dimensions = parameters['dimensions']

        self.best_gene = None
        self.best_score = 0

        # stałe (to można potencjalnie potem przekazać jako dataclass do konstruktora)
        self.total_generations = total_generations
        self.population_size = 100
        self.selection_rate = 0.5

        self.crossover_elitism_rate = 0.2

        self.mutation_rate = 0.75
        self.mutation_swap_rate = 0.1
        self.mutation_jitter_stdev = 1.5

        self.tickcount = 100
    
    def save_best_gene_to_json(self, filename):
        result = generate_paths_for_all_drones(self.drones, self.best_gene)
        simulation_json_generator(filename, result[0], result[1], parameters)

    def run(self):
        self.initialize_population()
        yield self.population
        
        for _ in range(self.total_generations):
            self.step_generation()
            yield self.population
    
    def initialize_population(self):
        self.population = [generate_first_gen(self.objects, self.drones)
                            for _ in range(self.population_size)]
    
    def step_generation(self):
        best_candidates = self.selection()

        best_score_generation = best_candidates[0][1]
        print(f"generation {self.generation_number+1} best score: {best_score_generation}")
        self.record_best_gene(best_candidates[0])

        new_population = self.crossover(best_candidates)

        self.population = self.mutate(new_population)

        self.generation_number += 1
    
    def record_best_gene(self, candidate):
        if candidate[1] > self.best_score:
            self.best_gene, self.best_score = candidate
    
    def selection(self):
        # na podsatwie fitnessów wybieramy najlepszą część populacji (albo top n, albo np losowo z wagami fitness)
        fitnesses = self.calculate_fitness_population()
        fitnesses.sort(key=lambda x: x[1], reverse=True)

        pool_size = int(len(fitnesses) * self.selection_rate)
        return fitnesses[:pool_size] # top n
    
    def calculate_fitness_population(self):
        return [(gene, self.calculate_fitness_gene(gene)) 
                for gene in self.population]

    def calculate_fitness_gene(self, gene):
        current_positions = [drone.starting_position for drone in self.drones]
        object_scores = [0] * len(self.objects)
        first_paths, loop_paths = generate_paths_for_all_drones(self.drones, gene)

        for tick in range(self.tickcount):
            self.calculate_tick_scores(current_positions, object_scores)
            self.move_drones(current_positions, tick, first_paths, loop_paths)
        
        return min(object_scores)
    
    def calculate_tick_scores(self, current_positions, object_scores):
        for i, obj in enumerate(self.objects):
            covered_cells = self.get_covered_cells(obj, current_positions)
            object_scores[i] += self.calculate_object_score(covered_cells, len(obj))
    
    def get_covered_cells(self, obj, current_positions):
        return sum(
            1 for cell in obj
            if any(self.check_cell_coverage(drone, pos, cell)
                   for drone, pos in zip(self.drones, current_positions))
        )
    
    @staticmethod
    def check_cell_coverage(drone, drone_pos, cell):
        dist = max(abs(drone_pos[0] - cell[0]), abs(drone_pos[1] - cell[1]))
        return dist <= drone.radius
    
    @staticmethod
    def calculate_object_score(covered_cells, total_cells):
        if covered_cells == total_cells:
            return 1.0

        coverage_ratio = covered_cells / total_cells
        coverage_tier = coverage_ratio // 0.1
        score_exponent = coverage_tier - 9
        
        return 0.2 * pow(2, score_exponent)
    
    def move_drones(self, current_positions, tick, first_paths, loop_paths):
        time = tick + 1
        for i, drone in enumerate(self.drones):
            if time % drone.tickspeed == 0:
                moves = time // drone.tickspeed

                current_positions[i] = self.determine_position(
                    moves, 
                    first_paths[i], 
                    loop_paths[i]
                )
    
    @staticmethod
    def determine_position(moves, initial_path, loop_path):
        if moves < len(initial_path):
            return initial_path[moves]
        
        moves_in_loop = moves - len(initial_path)
        loop_index = moves_in_loop % len(loop_path)
        
        return loop_path[loop_index]

    def crossover(self, pool):
        new_population = []
        candidates = [x[0] for x in pool]
        weights = [x[1] for x in pool]

        for _ in range(self.population_size):
            mom = 0
            dad = 0
            while mom == dad:
                mom, dad = random.choices(candidates, weights=weights, k=2)
            
            new_gene = self.crossover_two_genes(mom, dad)
            new_population.append(new_gene)

        return new_population

    def crossover_two_genes(self, gene1, gene2):
        if random.random() < 2: # ! self.crossover_elitism_rate: - TO WYŁĄCZA KRZYŻÓWKĘ
            return copy.deepcopy(random.choice([gene1, gene2]))
        
        return [self.crossover_two_paths(p1, p2) for p1, p2 in zip(gene1, gene2)]

    def crossover_two_paths(self, path1, path2):
        '''
        Moje i czata pomysły:
        1. Zamiana podciągu u jednego rodzica, z drugiego rodzica
        2. 

        A -> | B -> C -> D | -> E
        A' -> B' -> | C' -> D' | -> E'

        A -> C' -> D' -> E
        '''
        pass

    def mutate(self, population):
        return [self.mutate_gene(gene) for gene in population]

    def mutate_gene(self, gene):
        if random.random() < self.mutation_rate:
            return gene
        
        new_gene = [self.mutate_path(path) for path in gene]
        
        if random.random() < self.mutation_swap_rate:
            self.swap_paths(new_gene)

        return new_gene
    
    def swap_paths(self, gene):
        idx1, idx2 = random.sample(range(len(gene)), 2)
        gene[idx1], gene[idx2] = gene[idx2], gene[idx1]
        
    def mutate_path(self, path):
        '''
        Moje pomysły na mutacje:
        1. Przesunięcie punktu według jakiegoś rozkładu
        2. Zmiana punkt na totalnie inny losowy
        3. Dodanie nowego losowego punktu dowolnie w sekwencji
        4. Dodanie nowego punktu pomiędzy dwoma instniejącymi
        5. Usunięcie dowolnego punktu (musi być rzadziej niż dodanie)
        6. Scramble kolejności jakiegoś podciągu punktów
        7. Rotacja punktów (w sensie ostatni -> 1, 1 -> 2, 2 -> 3, etc.)
        '''
        mutation_options = [
            self.nothing_mutation,
            self.point_jitter,
            self.random_point_reset,
            self.random_point_insertion,
            self.midpoint_insertion,
            self.point_deletion,
            self.slice_reversion
        ]

        weights = [15, 35, 10, 10, 15, 10, 5]

        mutation_func = random.choices(mutation_options, weights=weights, k=1)[0]
        return mutation_func(path)
    
    def nothing_mutation(self, path):
        return path

    def point_jitter(self, path):
        point_idx = random.randrange(0, len(path))

        dx = int(random.gauss(0, self.mutation_jitter_stdev))
        dy = int(random.gauss(0, self.mutation_jitter_stdev))

        x, y = path[point_idx]

        path[point_idx] = x+dx, y+dy

        return path
    
    def random_point_reset(self, path):
        point_idx = random.randrange(0, len(path))

        path[point_idx] = random.randrange(0, self.dimensions[0]), random.randrange(0, self.dimensions[1])

        return path
    
    def random_point_insertion(self, path):
        point_idx = random.randrange(0, len(path)+1)
        path.insert(point_idx, (random.randrange(0, self.dimensions[0]), random.randrange(0, self.dimensions[1])))
        
        return path

    def midpoint_insertion(self, path):
        point_idx = random.randrange(0, len(path))
        p1 = path[point_idx]
        p2 = path[(point_idx+1) % len(path)]

        if p1 != p2: # nwm czy to konieczne ale chyba warto mieć
            midpoint = (p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2
            path.insert(point_idx+1, midpoint)

        return path

    def point_deletion(self, path):
        if len(path) <= 2:
            return path

        point_idx = random.randrange(0, len(path))
        
        path.pop(point_idx)

        return path

    def slice_reversion(self, path):
        if len(path) <= 1:
            return path

        idx1 = random.randrange(len(path))
        idx2 = random.randrange(len(path))

        start = min(idx1, idx2)
        end = max(idx1, idx2)

        frame = path[start:end]
        frame.reverse()

        path[start:end] = frame

        return path


if __name__ == '__main__':
    random.seed(1)
    filename = sys.argv[1]
    parameters = parameters_parser(f"../shared/parameters_{filename}.json")
    evolution = Evolution(parameters, 100)
    for i in evolution.run():
        pass
    evolution.save_best_gene_to_json(f"../shared/simulation_{filename}.json")