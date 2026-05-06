from first_gen import generate_first_gen
from path_generator import generate_paths_for_all_drones
from json_parser import parameters_parser, simulation_json_generator
import random
import sys

class Evolution:
    def __init__(self, parameters, total_generations):
        self.population = []
        self.generation_number = 0

        self.drones = parameters['drones']
        self.objects = parameters['objects']
        self.dimensions = parameters['dimensions']

        # stałe (to można potencjalnie potem przekazać jako dataclass do konstruktora)
        self.total_generations = total_generations
        self.population_size = 100
        self.selection_rate = 0.5

        self.mutation_rate = 0.75
        self.mutation_jitter_stdev = 1.5

        self.tickcount = 10000

    def run(self):
        self.initialize_population()
        yield self.population
        
        for i in range(self.total_generations):
            self.step_generation()
            yield self.population
    
    def initialize_population(self):
        self.population = [generate_first_gen(self.objects, self.drones)
                            for _ in range(self.population_size)]
    
    def step_generation():
        best_genes = self.selection()

        new_population = self.crossover(best_genes)

        self.population = self.mutate(new_population)

        self.generation_number += 1
    
    def calculate_fitness_population(self):
        # bierzemy populacje, i dla każdego genu liczymy ten najdłuższy czas niepokrycia
        # normalizujemy jakoś i zwracamy jako krotka (index_w_populacji, fitness)
        # fitness to będzie minimum z wyniku każdego obiektu. Wynik to suma pokryć penalizowana przez procent niepokrycia
        fitnesses = []
        for i, gene in enumerate(self.population):
            fitnesses.append((i, self.calculate_fitness_gene(gene)))
        return fitnesses

    def calculate_fitness_gene(self, gene):
        current_drone_pos = [drone.starting_position for drone in self.drones]
        object_scores = [0] * len(self.objects)
        first_paths, loop_paths = generate_paths_for_all_drones(self.drones, gene)
        for tick in range(self.tickcount):
            for i, obj in enumerate(self.objects):
                covered_cells = 0
                object_cells = len(obj)
                for cell in obj:
                    for drone, pos in zip(self.drones, current_drone_pos):
                        if self.check_object_coverage(drone, pos, cell):
                            break
                    else:
                        continue
                    
                    covered_cells += 1
                
                if covered_cells == object_cells:
                    object_scores[i] += 1
                else:
                    coverage_ratio = covered_cells / object_cells
                    object_scores[i] += 0.2 * pow(2, coverage_ratio//0.1-9) # magia
            
            for i, drone in enumerate(self.drones):
                if (tick + 1) % drone.tickspeed == 0:
                    move_count = (tick + 1) // drone.tickspeed
                    if move_count < len(first_paths[i]):
                        current_drone_pos[i] = first_paths[i][move_count]
                    else:
                        current_drone_pos[i] = loop_paths[i][(move_count - len(first_paths[i])) % len(loop_paths[i])]
                    
        print(object_scores)
        return min(object_scores)

    @staticmethod
    def check_object_coverage(drone, drone_pos, cell):
        dist = max(abs(drone_pos[0] - cell[0]), abs(drone_pos[1] - cell[1]))
        return dist <= drone.radius

    def selection(self):
        # na podsatwie fitnessów wybieramy najlepszą część populacji (albo top n, albo np losowo z wagami fitness)
        fitnesses = self.calculate_fitness_population()
        fitnesses.sort(key=lambda x: x[1], reversed=True)
        n = len(fitnesses) * self.selection_rate
        return fitnesses[:n] # top n

    def crossover(self, pool):
        # nie wszystkie powinny się tu skrossować, chcemy raczej z małą szansą zostawiać geny takie jakie są
        pass

    def mutate(self, population):
        pass
    
    @staticmethod
    def crossover_two_genes(gene1, gene2):
        pass

    @staticmethod
    def mutate_gene(gene):
        if random.random() > mutation_rate:
            return gene
        
        new_gene = []
        for path in gene:
            new_gene.append(self.mutate_path(path))
        return new_gene
        
    @staticmethod
    def mutate_path(path):
        '''
        Moje pomysły na mutacje:
        1. Przesunięcie punktu według jakiegoś rozkładu
        2. Zmiana punkt na totalnie inny losowy
        3. Dodanie nowego losowego punktu dowolnie w sekwencji
        4. Dodanie nowego punktu jakoś pomiędzy dwoma instniejącymi (można dodać punkt na odcinku i go przesunąć lekko prostopadle)
        5. Usunięcie dowolnego punktu (musi być rzadziej niż dodanie)
        6. Odwrócenie kolejności waypointów (rzadkie)
        7. Scramble kolejności jakiegoś podciągu punktów
        8. Rotacja punktów (w sensie ostatni -> 1, 1 -> 2, 2 -> 3, etc.)
        '''
        mutation_options = [
            self.nothing_mutation,
            self.point_jitter
        ]

        weights = [1, 3]

        mutation_func = random.choices(mutation_options, weights=weights)[0]
        return mutation_func(path)
    
    @staticmethod
    def nothing_mutation(path):
        return path

    @staticmethod
    def point_jitter(path):
        pass

if __name__ == '__main__':
    random.seed(1)
    filename = sys.argv[1]
    parameters = parameters_parser(f"../shared/parameters_{filename}.json")
    evolution = Evolution(parameters, 100)
    evolution.initialize_population()
    import time
    s = time.perf_counter()
    print(evolution.calculate_fitness_population())
    print(time.perf_counter() - s)
    result = generate_paths_for_all_drones(evolution.drones, evolution.population[0])
    # simulation_json_generator(f"../shared/simulation_{filename}.json", result[0], result[1], parameters)