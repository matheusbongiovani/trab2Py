import sys
import time
import random
import matplotlib.pyplot as plt

#Classe Gene, que representa as cidades da instância.
class Gene(object):
    def __init__(self, x=0, y=0, z=0, id=0):
        self.x = x
        self.y = y
        self.z = z
        self.id = id
    # Posteriormente anexado à matriz de distancias reduzindo contas repitidas
    def distance(self, p):
        dx = self.x - p.x
        dy = self.y - p.y
        return ((dx**2) + (dy**2))**0.5


    def __str__(self):
        return 'id:' + str(self.id) + ' (' + str(self.x) + ',' + str(
            self.y) + ')' + ' demand:' + str(self.z)
    
    def __repr__(self):
        return str(self.id)

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return ((self.id) < (other.id))


start_time = time.time()
# cada meta-heurística possui um conjunto de parâmetros cujos
# valores devem ser fornecidos pela entrada
if len(sys.argv) != 2:
    print('----------------------ERROR----------------------')
    print('Sintaxe: python3 "program.py" "instância.vrp" "população" "prob mutação(%)" ')
    sys.exit('-------------------------------------------------')
else:
    arg1 = sys.argv[1]
    arg_mutate = 5/100
    
# arg_size = 64*2  # nºcidades-depot * 2

time_to_execute = 30   # Tempo de execução do algoritmo em segundos

header_array = []
array_of_genes = []

index_entrada = 0
with open(arg1, mode='r', encoding='utf-8') as file:
    num_linha = 0
    gene_coord_bool = False
    demand_section_bool = False

    for linha in file:
        # trecho para armazenar informações do cabeçalho
        if num_linha < 6:
            num_linha += 1
            splited = linha.split()
            header_array.append(splited[2])

        # trecho para pular linhas da entrada que não será utilizado
        if num_linha >= 6 and num_linha < 9:
            num_linha += 1
            if num_linha > 8:
                gene_coord_bool = True

        # trecho para armazenar as posições no vetor array_of_genes
        if gene_coord_bool:
            if linha.find('DEMAND_SECTION') != -1:
                gene_coord_bool = False
                demand_section_bool = True
            else:
                split_id_XY = linha.split()
                node = Gene(float(split_id_XY[1]), float(
                    split_id_XY[2]), id=(int(split_id_XY[0])-1))
                array_of_genes.append(node)

        # trecho para inserir a demanda de cada nó no vetor array_of_genes
        if demand_section_bool:
            if linha.find('DEMAND_SECTION') != -1:
                continue
            if linha.find('DEPOT_SECTION') != -1:
                demand_section_bool = False
            else:
                splitZ = linha.split()
                array_of_genes[index_entrada].z = float(splitZ[1])
                index_entrada += 1
# ---- fim da leitura da entrada ----


n_genes = index_entrada  # len(array_of_genes)
arg_size = (n_genes-1)*2


# obter valor K, que representa o número de veículos dado pela entrada
k_rotas = header_array[0].split('-k')
k_rotas = int(k_rotas[1])
k_cap_max = float(header_array[5])


def print_genes_list(genes_list):
    for gene in genes_list:
        print(gene.__str__())


def x_values(genes_list):
    list_x = []
    for gene in genes_list:
        list_x.append(gene.x)
    return list_x
    
def y_values(genes_list):
    list_y = []
    for gene in genes_list:
        list_y.append(gene.y)
    return list_y    


def func_matrix_distancias(genes):
    matrix_ij = []
    size = len(genes)
    for i in range(size):
        distancia = []
        for j in range(size):
            distancia.append(genes[i].distance(genes[j]))
        matrix_ij.append(distancia)
    return matrix_ij

matrix_distancias = func_matrix_distancias(array_of_genes)


#modelo fitness_solution([9, 3, 0, 2, 4, 0, 5, 6, 0, 8, 7, 1]) == Cromossomo
#os depots no meio do vetor já estão inseridos, precisamos adicionar o 1º e o último
def fitness(solution):
    cost = 0
    i = 0

    cost += matrix_distancias[0][solution[0].id]  #1º nó da 1ª rota
    for _ in range(len(solution)-1):
        cost += matrix_distancias[solution[i].id][solution[i+1].id]
        i += 1
    cost += matrix_distancias[solution[i].id][0] #último nó da última rota

    num_rotas_solucao = solution.count(array_of_genes[0]) +1
    
    if num_rotas_solucao != k_rotas:
        i = 0
        weight = 0
        penalty = 0
        while i < len(solution):
            weight += solution[i].z
            if solution[i].z == 0:
                if weight > k_cap_max:
                    # penalty*50 performed better
                    penalty += (weight - k_cap_max)*50
                    cost += penalty
                    weight = 0
            i += 1

    return cost

# tornar a solução factível, fazendo com que atenda as restrições do problema.
# solução inicial sempre vai ser factivel... Aplicar ela após mut/cross
def turn_feasible(cromo_entrada):
    genes_seq_entrada = array_of_genes.copy()
    genes_seq_entrada.pop(0)  # array com todas as cidades exceto o depot
    cromo = cromo_entrada.copy()
    
    # [1,2,3,0,1,2,4,0,2,1,1]
    
    for each in cromo:
        if each.id == 0:
            cromo.remove(each)
    
    # Trecho para remover eventuais cidades duplicadas e faltando, devido as mutações/crossOver
    adjust = True
    while adjust:
        adjust = False
        for i1 in range(len(cromo)):
            for i2 in range(i1):
                if cromo[i1] == cromo[i2]:
                    del_duplicated = True
                    for gene in genes_seq_entrada:
                        if gene not in cromo:
                            cromo[i1] = gene # cromo[i] recebe cidade(gene) 
                            del_duplicated = False # substitui cidade duplicada pela que esta faltando.
                            break
                    if del_duplicated:
                        del cromo[i1]
                    adjust = True
                if adjust: break
            if adjust: break

    # separar cidades em rotas # mudar jeito de como distribuir a demanda...
    total = 0.0
    i = 0   
    while i < len(cromo):
        total += cromo[i].z  #Se demanda de i exceder, o Depot é inserido imediatamente antes
        if total > k_cap_max:
            cromo.insert(i, array_of_genes[0])
            total = 0.0
        i += 1
        
    return cromo

def create_initial_population(genes_entrada, pop_size):
    population = []
    genes = genes_entrada.copy()
    genes.pop(0)  # dado a entrada, retiramos o depot

    for _ in range(int(pop_size)):
        randomized = random.sample(genes, len(genes))
        randomized = turn_feasible(randomized)
        population.append(randomized)

    return population


# modelo da entrada: [3,1,2,6,4,5,7,8,9]
def create_new_population(pop_inicial, mutate_prob=0.05):
    pop = pop_inicial.copy()
    new_pop = []

    # mutação de inverter trecho do vetor
    def mutation(cromo, prob_mutate):
        if random.random() < float(prob_mutate):

            index1 = random.randrange(0,len(cromo))
            index2 = random.randrange(index1,len(cromo))
            
            mid = cromo[index1:index2]
            mid.reverse()
            
            result = cromo[0:index1] + mid + cromo[index2:]
            return result     
        else:
            return cromo 

    def tournament_select_two(old_pop):
        def best_fit_parents():
            selecteds = []
            num_selects = int(len(old_pop)/10) # selecionar num_pop/10 elems.
            candidates = random.sample(old_pop, num_selects)
            best = 999999999  # very large number to always have a better fitness
            for cromo in candidates:
                fitness_value = fitness(cromo)
                if fitness_value < best:
                    selecteds.append(cromo)
                    best = fitness_value
            best_cromo = selecteds.pop()
            return best_cromo
        
        parent1 = best_fit_parents()
        parent2 = best_fit_parents()
        
        return [parent1, parent2]
    
    def crossover_mutate_and_add_to_new_generation(parent1, parent2):
        # filhos serão construídos através de cortes nos vetores dos pais
        cut1, cut2 = random.randrange(len(parent1)), random.randrange(len(parent2))
        cut1, cut2 = min(cut1, cut2), max(cut1, cut2)

        child1 = parent1[:cut1] + parent2[cut1:cut2] + parent1[cut2:]
        child2 = parent2[:cut1] + parent1[cut1:cut2] + parent2[cut2:]


        child1 = mutation(child1, mutate_prob)
        child1 = mutation(child1, mutate_prob)

        child1 = turn_feasible(child1)
        child2 = turn_feasible(child2)

        new_pop.append(child1)
        new_pop.append(child2)

    # Para termos a população constante, iteramos o tamanho da população divido por 2
    # já que em cada iteração são gerado 2 membros da nova geração
    tamanhoSobreDois = int(len(pop)/2)
    for _ in range(tamanhoSobreDois):
        parent1, parent2 = tournament_select_two(pop)
        crossover_mutate_and_add_to_new_generation(parent1, parent2)

    return new_pop


def inicializar():
    population = create_initial_population(array_of_genes,arg_size)

    index_geracao_atual = 0
    iteracoes_sem_melhora = 0
    num_iteracoes_melhor_solucao = 0
    best_solution_global = population[0] #tem que iniciar com algum valor
    best_fitness_global = 99999999999
    best_fitness_atual = 99999999999
    execution_time = time.time()

    while True:
        population = create_new_population(population)
        index_geracao_atual += 1
        best_fitness_atual = 99999999999
        best_solution_atual = None

        # Passar a salvar custo das iterações (best fitness) para gerar gráficos
        # é bom saber também exatamente qual iteração obteve o melhor fitness...
        for solution in population:
            fit_value = fitness(solution)
            if fit_value < best_fitness_atual:
                best_fitness_atual = fit_value
                best_solution_atual = solution
        
        if best_fitness_atual >= best_fitness_global:
            iteracoes_sem_melhora += 1
            mutate_prob += 0.01
        else:
            best_solution_global = best_solution_atual
            best_fitness_global = best_fitness_atual
            num_iteracoes_melhor_solucao = index_geracao_atual
            time_to_best_solution = time.time() - start_time
            iteracoes_sem_melhora = 0
            mutate_prob = 0.05


        # se tiver 100 iterações sem melhora, reseta prob. de mutação
        if iteracoes_sem_melhora > 100:
            mutate_prob = 0.05


        # Checar o tempo de execução para anteder a condição de parada
        execution_time = time.time()
        time_elapsed = execution_time - start_time
        if time_elapsed > time_to_execute:
            break


    print('-----------------------------------------------------------------------------')
    print(f'fitness melhor entre todas gerações:{fitness(best_solution_global)}, melhor fitness atual: {fitness(best_solution_atual)}')
    print(f'num de iterações: {index_geracao_atual}, iterações sem melhora:{iteracoes_sem_melhora}, iterações pra melhor solução: {num_iteracoes_melhor_solucao}, tempo de exc da melhor solução: {time_to_best_solution}')

    return best_solution_global



best_reached_solution = inicializar()

# # # ----------------------------------------
end_time = time.time()
print("Tempo de execução:", end_time-start_time)
# # # ----------------------------------------


##---------------------------PLOTING ZONE------------------------
def route_demands(solution):
    rotas = solution.copy()
    demanda_rotas = []
    demanda = 0.0
    for gene in rotas:
        demanda += gene.z
        if gene.id == 0 and demanda != 0:
            demanda_rotas.append(demanda)
            demanda = 0
    demanda_rotas.append(demanda)
    return demanda_rotas

plot_sol = best_reached_solution.copy()
plot_sol.insert(0,array_of_genes[0])
num_veiculos_usados_na_solucao = plot_sol.count(array_of_genes[0])
plot_sol.append(array_of_genes[0])

if num_veiculos_usados_na_solucao != k_rotas:
    print('NOT ENOUGH TIME TO FIND A FEASIBLE SOLUTION!')
    print('CURRENT SOLUTION PROBABLY USES MORE VEHICLES THAN THE MINIMUM POSSIBLE!')
    print('THIS INSTANCE MIGHT REQUIRE A LONGER COMPUTATIONAL TIME')

print(f'num of vehicles used in solution: {num_veiculos_usados_na_solucao}')
print(f'Número mínimo de veículos(rotas): {k_rotas}')
print(f'Capacidade máxima do veículo: {k_cap_max}')
print(f'Demanda das rotas {route_demands(best_reached_solution)}')
cities_sum_demands = sum([gene.z for gene in array_of_genes])
print(f'Demanda total das cidades: {cities_sum_demands}')



# # # # # plt.xkcd()  # deixar visual de quadrinho
# # # ----------- plot section---------------
plt.grid(False)
plt.scatter(x_values(array_of_genes), y_values(
    array_of_genes), s=20, c='blue')
plt.scatter(array_of_genes[0].x, array_of_genes[0].y, s=35, c='black')
# def plot_solution(solution):
#     for rota in solution:
#         plt.plot(x_values(rota),y_values(rota))


print(f'plot_sol: {plot_sol}, fitness:{fitness(best_reached_solution)}')
list_to_plot = []
for each in plot_sol:
    list_to_plot.append(each)
    if each.id == 0:
        list_to_plot.append(array_of_genes[0])
        plt.plot(x_values(list_to_plot),y_values(list_to_plot))
        list_to_plot.clear()
        list_to_plot.append(array_of_genes[0])


plt.show()

