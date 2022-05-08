import pygad
import numpy
import Box

"""
 TODO - implement Genetic Algorithm

"""


def get_data():
    pass


packges = get_data()

L, W, H = (600, 200, 200)
N = 8  # len(packges)
NUM_OF_CHROM = 100
NUM_OF_ITER = 1
# layer options
LAYER_TYPE = {0: ("l", "w", "h"), 1: ("w", "l", "h"), 2: ("l", "h", "w"), 3: ("h", "l", "w"), 4: ("w", "h", "l"),
              5: ("h", "w", "l")}
LAYER_TYPE_UP_ARROW = {0: ("l", "w", "h"), 1: ("w", "l", "h")}


def generate_EMS():
    pass


def update_EMS():
    pass


def get_min_EMS():
    pass

# todo fitness func
def fitness_func(solution, solution_idx):
    fitness = N

    return fitness


def parent_selection_func(fitness, num_parents, ga_instance):
    fitness_sorted = sorted(range(len(fitness)), key=lambda k: fitness[k])
    fitness_sorted.reverse()

    parents = numpy.empty((num_parents, ga_instance.population.shape[1]))

    for parent_num in range(num_parents):
        parents[parent_num, :] = ga_instance.population[fitness_sorted[parent_num], :].copy()

    return parents, fitness_sorted[:num_parents]


def crossover_func(parents, offspring_size, ga_instance):
    offspring = []
    idx = 0
    while len(offspring) != offspring_size[0]:
        parent1 = parents[idx % parents.shape[0], :].copy()
        parent2 = parents[(idx + 1) % parents.shape[0], :].copy()

        random_split_point = numpy.random.choice(range(offspring_size[1]))

        parent1[random_split_point:] = parent2[random_split_point:]

        offspring.append(parent1)

        idx += 1

    return numpy.array(offspring)


def mutation_func(offspring, ga_instance):
    for chromosome_idx in range(offspring.shape[0]):
        probs = numpy.random.random(size=offspring.shape[1])
        for gene_idx in range(offspring.shape[1]):
            if probs[gene_idx] <= ga_instance.mutation_probability:
                random_value = int(numpy.random.uniform(1, N + 1))
                random_value_idx = numpy.where(offspring[chromosome_idx] == random_value)
                offspring[chromosome_idx, gene_idx], offspring[chromosome_idx, random_value_idx] = random_value, \
                                                                                                   offspring[
                                                                                                       chromosome_idx, gene_idx]

    return offspring


def get_layer(prob):
    res = prob
    if 0 <= prob < (1 / 6):
        res = 0
    elif 1 / 6 <= prob < (2 / 6):
        res = 1
    elif 2 / 6 <= prob < 0.5:
        res = 2
    elif 0.5 <= prob < (4 / 6):
        res = 3
    elif 4 / 6 <= prob < (5 / 6):
        res = 4
    elif 5 / 6 <= prob < 1:
        res = 5

    return res


def init_population_random():
    # initialize population

    init_pop = numpy.full((NUM_OF_CHROM, 2*N), 0)
    for i in range(NUM_OF_CHROM):

        random_prob_bps = numpy.random.random(size=N)
        random_prob_blt = numpy.random.random(size=N)
        box_pack_seq = sorted(range(N), key=lambda k: random_prob_bps[k], reverse=True)
        box_layer_type = [get_layer(k) for k in random_prob_blt]
        init_pop[i] = numpy.array(box_pack_seq + box_layer_type)
    print("debug")


def on_generation_func(ga_instance):
    # solution, solution_fitness, solution_idx = ga_instance.best_solution(ga_instance.last_generation_fitness)
    pop_fitness = ga_instance.last_generation_fitness
    best_match_idx = numpy.where(pop_fitness == numpy.max(pop_fitness))[0]

    best_solution = ga_instance.population[best_match_idx, :].copy()
    best_solution_fitness = pop_fitness[best_match_idx]
    # if best_solution_fitness[0] == N:
    #     for i in range(best_solution.shape[0]):


for i in range(NUM_OF_ITER):
    ga_instance = pygad.GA(num_generations=200,
                           sol_per_pop=NUM_OF_CHROM,
                           num_parents_mating=20,
                           num_genes=N,
                           gene_type=int,
                           gene_space=range(1, N + 1),
                           # allow_duplicate_genes=False,
                           crossover_type=crossover_func,
                           mutation_type=mutation_func,
                           mutation_probability=0.2,
                           parent_selection_type=parent_selection_func,
                           keep_parents=2,
                           initial_population=init_population_random(),
                           on_generation=on_generation_func,

                           fitness_func=fitness_func)
    ga_instance.run()

    ga_instance.plot_fitness()

    solution, solution_fitness, solution_idx = ga_instance.best_solution(ga_instance.last_generation_fitness)
    print("Parameters of the best solution : {solution}".format(solution=solution))
    print("Fitness value of the best solution = {solution_fitness}".format(solution_fitness=solution_fitness))
    print("Index of the best solution : {solution_idx}".format(solution_idx=solution_idx))
    print("last fitness : {fitness}".format(fitness=ga_instance.last_generation_fitness))
