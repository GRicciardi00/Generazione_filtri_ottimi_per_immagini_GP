#    This file is part of EAP.
#
#    EAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    EAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with EAP. If not, see <http://www.gnu.org/licenses/>.


import operator, random, sys, multiprocessing, numpy, pickle, os, time, math,glob
import pygraphviz as pgv

from deap import algorithms
from deap import base
from deap import creator
from deap import tools
from deap import gp

def crop(img):
    y,x = img.shape
    startx = (random.randint(0, x-30))
    starty = (random.randint(0, y-30))
    results = [0,0,0]   
    results[0] = img[starty:starty+30,startx:startx+30]
    results[1] = startx
    results[2] = starty
    result_noborder = results[0][2:-2, 2:-2]
    return results
    
def crop_label(img,startx,starty):
    return img[starty:starty+30,startx:startx+30]   
    
    
#MAIN
path_original = 'dataset/train/train_denoise/noise' #Full images folder
path_expected = 'dataset/train/train_denoise' #Expected images folder 
SIZE = 30  #image size
file_name = sys.argv[1].split("/")[-1]
file_name = os.path.splitext(file_name)[0]
input_images = []
result_images = []
#taking windows from images
for i in range (10):
	filename=random.choice(os.listdir(path_original))
	while ".txt" not in filename:
		filename=random.choice(os.listdir(path_original))
	img_input = numpy.loadtxt(path_original + "/" + filename)
	img_label = numpy.loadtxt(path_expected + "/" + filename)
	cropped = crop(img_input)
	input_sample = cropped[0]
	startx = cropped[1]
	starty = cropped[2]
	result_sample = crop_label(img_label,startx,starty)
	input_images.append(input_sample)
	result_images.append(result_sample)
input_images = numpy.array(input_images)
result_images = numpy.array(result_images)
#GP PARAMENTERS: crossover prob, mutation prob, number of generation, population size: change at will!
CXPB, MUTPB, NGEN, POPSIZE, MAXDEPTH = 0.3, 0.4, 40, 400, 8
#LOGGING PARAMETERS
FREQ_SAVE = 10

# Define new functions

#TODO: define function to be used by GP. These will be the branches of GP.

def safeadd(a,b):
    s = a + b
    if s >= 255:
        s =255
    return s
    
def safesub(a, b):
    s = a - b
    if s < 0:
        s = 0
    return s
    
def safemul(a, b):
    s = a * b
    if s < 0:
        s = 0
    if s > 255:
        s = 255
    return s

def safediv(a, b):
    if b == 0:
    	return 0
    try:
        s = a / b
    except:
        return 0
    if s <= -255:
        return -255
    if s >= 255:
        return 255

def avg2(a, b):
    try:
        return (a + b) / 2
    except:
        return 0

def avg3(a, b, c):
    try:
        return (a + b + c) / 3
    except:
        return 0
        
#TODO create a "PrimitiveSet": add the previously created function to your pool
pset = gp.PrimitiveSet("MAIN",25)
pset.addPrimitive(safeadd,2)
pset.addPrimitive(safesub,2)
pset.addPrimitive(safediv,2)
pset.addPrimitive(safemul,2)
pset.addPrimitive(avg2,2)
pset.addPrimitive(avg3,3)

#TODO define the number of "arguments", your variables that will bring your dataset to the GP
#TODO define the number of "arguments", your variables that will bring your dataset to the GP
pset.renameArguments(ARG0='x0y0')
pset.renameArguments(ARG1='x0y')
pset.renameArguments(ARG2='x0y1')
pset.renameArguments(ARG3='x0y2')
pset.renameArguments(ARG4='x0y3')
pset.renameArguments(ARG5='xy0')
pset.renameArguments(ARG6='xy')
pset.renameArguments(ARG7='xy1')
pset.renameArguments(ARG8='xy2')
pset.renameArguments(ARG9='xy3')
pset.renameArguments(ARG10='x1y0')
pset.renameArguments(ARG11='x1y')
pset.renameArguments(ARG12='x1y1')
pset.renameArguments(ARG13='x1y2')
pset.renameArguments(ARG14='x1y3')
pset.renameArguments(ARG15='x2y0')
pset.renameArguments(ARG16='x2y')
pset.renameArguments(ARG17='x2y1')
pset.renameArguments(ARG18='x2y2')
pset.renameArguments(ARG19='x2y3')
pset.renameArguments(ARG20='x3y0')
pset.renameArguments(ARG21='x3y')
pset.renameArguments(ARG22='x3y1')
pset.renameArguments(ARG23='x3y2')
pset.renameArguments(ARG24='x3y3')

#TODO: create constants and arguments, the "leaves" of the GP.
pset.addEphemeralConstant('rand30', lambda: random.randint(1,30))
pset.addEphemeralConstant('rand01', lambda: random.randint(0,1))
pset.addEphemeralConstant('rand255', lambda: random.randint(0,255))
#TODO: define Fitness
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))

#TODO: define GP individual type
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMin)

#TODO: define specific GP options like how to...
#generate an individual
#a population
#how to evaluate it
#perform the SELECTION
#mating
#generation of mutated branches
toolbox = base.Toolbox()
toolbox.register("expr", gp.genHalfAndHalf, pset=pset, min_=1, max_=3)
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("compile", gp.compile, pset=pset)

#TODO (IMP): define the fitness: how to evaluate an individual
def evalImage(individual, points):
    func = toolbox.compile(expr=individual)
    sqerror_total=0
    for image in range(len(input_images)):
        sqerror_single = 0
        input_sample = input_images[image]
        #print(input_sample.shape) 30x30 OK
        result_sample = result_images[image]
        #print(result_sample.shape) 30x30 OK
        result_GP =numpy.zeros((SIZE,SIZE),dtype=int)
        for p in points:
            try:
                result_GP[p] = func(input_sample[p[0]-2,p[1]-2],
                                    input_sample[p[0]-2,p[1]-1],
            			    input_sample[p[0]-2,p[1]],
            			    input_sample[p[0]-2,p[1]+1],
            			    input_sample[p[0]-2,p[0]+2],
            			    input_sample[p[0]-1,p[1]-2],
           			    input_sample[p[0]-1,p[1]-1],
           			    input_sample[p[0]-1,p[1]],
            			    input_sample[p[0]-1,p[1]+1],
            			    input_sample[p[0]-1,p[1]+2],
            			    input_sample[p[0],p[1]-2],
            			    input_sample[p[0],p[1]-1],
            			    input_sample[p],
				    input_sample[p[0],p[1]+1],
				    input_sample[p[0],p[1]+2],
				    input_sample[p[0]+1,p[1]-2],
				    input_sample[p[0]+1,p[1]-1],
				    input_sample[p[0]+1,p[1]],
				    input_sample[p[0]+1,p[1]+1],
				    input_sample[p[0]+1,p[1]+2],
				    input_sample[p[0]+2,p[1]-2],
				    input_sample[p[0]+2,p[1]-1],
				    input_sample[p[0]+2,p[1]],
				    input_sample[p[0]+2,p[1]+1],
				    input_sample[p[0]+2,p[1]+2]
			    	 )
            except:
                result_GP[p]=1
            for pi in points:
                try:
                    sqerror_single += numpy.power( ( result_GP[pi] - result_sample[pi]), 2)
                except:
                    sqerror_single += 1000.0
            sqerror_total += sqerror_single/len(points)
    return sqerror_total,

    

    
    
        
toolbox.register("evaluate", evalImage, points=[(y,x) for y in range(1,SIZE-2) for x in range(1,SIZE-2)])
toolbox.register("select", tools.selTournament, tournsize=5)
toolbox.register("mate",gp.cxOnePoint)
toolbox.register("expr_mut", gp.genFull, min_=1, max_=3)
toolbox.register("mutate",gp.mutUniform,expr=toolbox.expr_mut, pset=pset)

toolbox.decorate("mate", gp.staticLimit(key=operator.attrgetter("height"), max_value = MAXDEPTH))
toolbox.decorate("mutate", gp.staticLimit(key=operator.attrgetter("height"), max_value = MAXDEPTH))

# ENABLE PARALLEL PROCESSING
pool = multiprocessing.Pool()
toolbox.register("map", pool.map)

#main program
def main():
    
    #create unique location where to store the experiment
    t = time.localtime()
    TIMEPOST = str(t.tm_year) + str(t.tm_mon) + str(t.tm_mday) + "_"+ str(t.tm_hour) + str(t.tm_min) + str(t.tm_sec)
    OUTPUTDIR = sys.argv[3] + "/Denoise_Execution_" + TIMEPOST
    print ("creating directory " + OUTPUTDIR)
    os.mkdir(OUTPUTDIR)


    # Start a new evolution with an initial random population of individuals
    population = toolbox.population(n=POPSIZE)
    start_gen = 0
    #save the best of each generation: HallOfFame!
    halloffame = tools.HallOfFame(maxsize=3)
    #enable advanced logging
    logbook = tools.Logbook()

    #collect statistics about evolution
    stats_fit = tools.Statistics(lambda ind: ind.fitness.values)
    stats_size = tools.Statistics(len)
    mstats = tools.MultiStatistics(fitness=stats_fit, size=stats_size)
    mstats.register("avg", numpy.mean)
    mstats.register("std", numpy.std)
    mstats.register("min", numpy.min)
    mstats.register("max", numpy.max)

    #MAIN LOOP THAT WILL DRIVE THE EVOLUTION
    for gen in range(start_gen, NGEN): 
        
        #for each generation....
        #TODO import population
        population = algorithms.varAnd(population, toolbox, cxpb=CXPB, mutpb = MUTPB)
        #TODO check that every individual is valid (size constrains!)
        invalid_ind = [ind for ind in population if not ind.fitness.valid]
        #TODO evaluate and check fitness for each individual
        fitnesses = toolbox.map(toolbox.evaluate,invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
            
        #TODO update hall of fame
        halloffame.update(population)
        #TODO update statistics
        record = mstats.compile(population)
        #TODO update logbook
        logbook.record(gen=gen,evals=len(invalid_ind), **record)
        print (logbook.stream)
        #print "\tBEST IND", halloffame[0]
        
       
        
        #select individuals from current population that will generate the next one
        population = toolbox.select(population, k=len(population))
                
        #save and plot current status
        if gen % FREQ_SAVE == 0 or gen == NGEN-1:
            #saving logbook
            print ("*************************** SAVING LOGBOOK")
            cp = dict(logbook=logbook)
            with open(os.path.join(OUTPUTDIR,file_name +"_logbook.pkl"), "wb") as cp_file:
                pickle.dump(cp, cp_file)
                
            with open(os.path.join(OUTPUTDIR,file_name + "_best.txt"), "w") as bestfile:
                bestfile.write(str(halloffame[0]))
                
            with open(os.path.join(OUTPUTDIR,file_name + "_best2.txt"), "w") as bestfile:
                bestfile.write(str(halloffame[1]))
                
            with open(os.path.join(OUTPUTDIR,file_name + "_best3.txt"), "w") as bestfile:
                bestfile.write(str(halloffame[2]))    
            
            cp = dict(best=str(halloffame[0]), datanoisename=sys.argv[1], time=TIMEPOST )
            with open(os.path.join(OUTPUTDIR,file_name + "_best.pkl"), "wb") as bestfile:
                pickle.dump(cp, bestfile)
            cp = dict(best=str(halloffame[1]), datanoisename=sys.argv[1], time=TIMEPOST )
            with open(os.path.join(OUTPUTDIR,file_name + "_best2.pkl"), "wb") as bestfile:
                pickle.dump(cp, bestfile)
            cp = dict(best=str(halloffame[2]), datanoisename=sys.argv[1], time=TIMEPOST )
            with open(os.path.join(OUTPUTDIR,file_name + "_best3.pkl"), "wb") as bestfile:
                pickle.dump(cp, bestfile)
                
            #saving pdf graph of the best tree up to now
            nodes, edges, labels = gp.graph(halloffame[0])

            g = pgv.AGraph()
            g.add_nodes_from(nodes)
            g.add_edges_from(edges)
            g.layout(prog="dot")

            for i in nodes:
                n = g.get_node(i)
                n.attr["label"] = labels[i]
                
            g.draw( os.path.join(OUTPUTDIR,file_name +"_" + str(gen) + ".pdf") )
                                


    print ('-------------------------------')
    print ('-------------------------------')
    print ('-------------------------------')
    print ('----- EVOLUTION FINISHED ------')
    print ('BEST 3 SOLUTIONS:')
    print ('----------FIRST----------')
    print (halloffame[0])
    print ('----------SECOND----------')
    print (halloffame[1])
    print ('----------THIRD----------')
    print (halloffame[2])
    print ('-------------------------------')

    
    return None
    

if __name__ == "__main__":
    main()
    sys.exit()
