import sys
import pdb
import time
import pickle
import sqlite3
import argparse
from math import factorial
from itertools import permutations
from random import Random
import random
from cStringIO import StringIO

RANDOM_SEED = 0
GENERATIONS_MAX = 1000
POPULATION_SIZE = 300
TERMINATE_STEPS = 200
BREED_CROSS   = 0.7
BREED_PROMOTE = 0.1
BREED_MUTATE  = 0.1
MUTATE_RATE   = 0.2
MUTATE_ACTION = 0.3
MUTATE_STATE  = 0.4


def dumps(camp, args, trail, name=None):
    "Dump critter information to create animated gif."
    chromo = camp.ranking[0][-1]
    dlog = []
    fitness_func = Fitness(trail, args)
    fitness_value = fitness_func(chromo, dlog=dlog)
    points = dlog[0]['points']
    for _ in dlog:
        del _['points']

    data = pickle.dumps({'ver':1.0, 'chromo':chromo, 'trail':trail,
                          'log':dlog, 'points':points, 'args':args,
                          'generation': camp.generation})
    if name:
        filename = "{0}-{1:2.5f}.log".format(name, fitness_value)
        w = open(filename, 'wt').write(data)
    return data

def loads(text):
    return pickle.loads(text)

class Critter(object):
    actions=('F','L','R')
    states=24

    def __init__(self, chromo=None, rand=None):
        self.chromo = chromo if chromo else self.create(rand)

    def __iter__(self):
        return iter(self.chromo)

    @staticmethod
    def create(random=Random):
        '''(no exist (action, next state), exist (action, next state)
        '''
        return [(
            # No exist in the square in front of it
            (random.choice(Critter.actions), random.randrange(0, Critter.states)),
            # exist in front
            (random.choice(Critter.actions), random.randrange(0, Critter.states)))
                for _ in range(Critter.states)]

    @staticmethod
    def crossover(parent0, parent1, *positions):
        """Create a new Chromosone from two parents.
        Chromo is made from parent1[0:position] + parent2[position:]
        """
        assert len(parent0) == len(parent1)
        start = 0
        chromo = []
        src = lambda x: parent0 if x % 2 == 0 else parent1
        positions = list(positions)
        positions.sort()
        for idx, end in enumerate(positions):
            #src = parent2 if end
            chromo.extend(src(idx)[start:end])
            start = end
        chromo.extend(src(idx+1)[start:])
        return chromo

    @staticmethod
    def crossover_uniform(parent0, parent1):
        """Randomly copy bits from parents to create new
        """
        chromo = []
        for state0, state1 in zip(parent0, parent1):
            chromo.append(state0 if random.random() < 0.5 else state1)
        return chromo

    @staticmethod
    def mutate(candidate, args, random=Random):
        """Mutate a candidate according to the following parameters
        :mutation_rate: probability against each state in candidate will mutate
        :mutate_action: probabilty states action will mutate
        :mutate_state: probabilty the next state will mutation
        """
        mut_rate = args.setdefault('mutate_rate', MUTATE_RATE)
        mut_action_rate = args.setdefault('mutate_action', MUTATE_ACTION)
        mut_state_rate = args.setdefault('mutate_state', MUTATE_STATE)
        mutant = candidate[:]
        for idx, state in enumerate(mutant):
            if random.random() < mut_rate:
                state = list(state)
                i = int(random.random() < 0.5)
                action, next_state = state[i]
                if random.random() < mut_action_rate:
                    action = random.choice(Critter.actions)
                if random.random() < mut_state_rate:
                    next_state = random.randrange(0, Critter.states)
                state[i] = (action, next_state)
                mutant[idx] = tuple(state)
        return mutant

    def analize(self, chromo):
        "List all states used"
        visited =set()
        to_visit = {0}
        while to_visit:
            state = to_visit.pop()
            visited.add(state)
            for action, next_state in chromo[state]:
                if next_state not in visited:
                    to_visit.add(next_state)
        return tuple(sorted(visited))

    def pprint(self, chromo, analized=None):
        """Pretty print chromo.
        If analized show where junk DNA is stored.
        """
        out = StringIO()
        groups_of = 4
        for idx in range(0, self.states, groups_of):
            for i in range(groups_of):
                exist, noexist = chromo[idx+i]
                try:
                    text = "{0:2d}: {1} {2:2d} {3} {4:2d}  ".format(
                            idx+i, exist[0], exist[1], noexist[0], noexist[1])
                except ValueError as err:
                    pdb.set_trace()
                try:
                    if idx+i not in analized:
                        text = text.lower().replace(' ', '-', 4)
                except:
                    pass
                out.write(text)
            out.write("\n")
        return out.getvalue()


class Fitness(object):
    turn_right = {(0,1): (1,0), (1,0): (0,-1), (0,-1): (-1,0), (-1,0): (0,1)}
    turn_left = {(0,1): (-1,0), (-1,0): (0,-1), (0,-1): (1,0), (1,0): (0,-1)}

    def __init__(self, trail, args):
        "Looking for 'terminate-steps' in args"
        self.trail = trail
        self.allowed_steps = args.setdefault('terminate-steps', TERMINATE_STEPS)

    def looking_at(self, current, direction):
        pos = (current[0]+direction[0], current[1]+direction[1])
        return pos

    def do_action(self, action, state, field):
        action, next_state = chromo[self.state]

    def terminate(self):
        return len(self.trail) == 0 or self.step > self.allowed_steps

    def __call__(self, chromo, log=None, dlog=None):
        "Returns (found, values)"
        self.step = -1
        self.state = 0
        self.pos = (0,0)
        self.looking = (0,1)
        points = []
        trail = self.trail.copy()
        while self.step < self.allowed_steps and len(trail):
            self.step += 1
            spot = self.looking_at(self.pos, self.looking)
            exist = int(spot in trail)
            action, next_state = chromo[self.state][exist]
            if log:
                log.write("[%3d:%2d] exist=%d (%s, %d) pos=%s look=%s)\n" %(
                            self.step, self.state, exist, action, next_state,
                            self.pos, spot))
            if dlog is not None:
                dlog.append({'state':self.state, 'pos':self.pos, 'exist': exist,
                             'looking':self.looking, 'points': points,
                             'action':action, 'next_state': next_state})
            if action == 'R':
                self.looking = self.turn_right[self.looking]
            elif action == 'L':
                self.looking = self.turn_left[self.looking]
            elif action == 'F':
                self.pos = spot
                if exist:
                    trail.remove(self.pos)
                    points.append(self.step)
            self.state = next_state
        if points:
            return (len(points) + float(self.allowed_steps - points[-1])/self.allowed_steps), self.step
        return 0, self.step

class Breeder(object):
    """
    ARGS
      population-size:
      breed-promote:0.1  Promote the top performers to the next round
      breed-mutate:0.1   Mutate from promoted
      breed-cross:.7     Cross breed from previous top population
        random breeding for whatever remains .1
    """
    def __init__(self, generator, args):
        self.generator = generator
        self.size = args['population-size']
        self.promote_cnt = int(self.size * args.setdefault('breed-promote', BREED_PROMOTE))
        self.mutate_cnt = min(self.promote_cnt, int(self.size * args.setdefault('breed-mutate', BREED_MUTATE)))
        self.cross_cnt   = int(self.size * args.setdefault('breed-cross', BREED_CROSS))
        self.random_cnt = self.size-max(0, (self.promote_cnt+self.mutate_cnt+self.cross_cnt))
        n = 3
        while factorial(n) < self.cross_cnt:
            n+=1
        self.permutations = n

    def __call__(self, fitness_chromo, random, args):
        next_gen = []
        # Promote 10%
        if self.promote_cnt:
            next_gen.extend([chromo for fit, chromo in fitness_chromo[:self.promote_cnt]])
        # Mutate promoted
        if self.mutate_cnt:
            next_gen.extend([Critter.mutate(_, args, random) for f, _ in fitness_chromo[:self.mutate_cnt]])
        # Random %10
        next_gen.extend([self.generator(random, args) for _ in xrange(self.random_cnt)])
        # Cross
        for idx, pairs in enumerate(permutations(fitness_chromo[:self.permutations], 2)):
            if idx >= self.cross_cnt:
                break
            (f0, p0), (f1, p1) = pairs
            next_gen.append(Critter.crossover(p0, p1, random.randint(0, Critter.states)))
        return next_gen


class BreedingCamp(object):
    def __init__(self, generator, fitness, evaluation, breader, random=None, args=None):
        """
        :generator: func(random, args)
            Create and return a single critter chromosone
        :fitness: func(candidates, args)
            Return a sequence fo fiteness for a sequence of candidates
        :evaluation: func(fitness_chromo pairs, random, args)
        :breading: func(fitness_chromo, random, args)
            Return a population-size of chromozones

        :ARGS:
        population-size:300 Population size
        random_seed:0 Seed random geneator
        generation-max:1000 Maximum generation before stopping

        """
        self.args = args
        self.random = random if random else Random(args.setdefault('random-seed', RANDOM_SEED))
        self.generation = 0
        self.generation_max = int(args.setdefault('generations-max', GENERATIONS_MAX))
        self.generator = generator
        self.fitness = fitness
        self.evaluation = evaluation
        self.breader = breader
        self.population = args.setdefault('population-size', POPULATION_SIZE)
        self.stable = [generator(self.random, args) for _ in xrange(self.population)]

    def evolve(self):
        ranking = None
        while self.generation < self.generation_max:
            fitness = self.fitness(self.stable, self.random, self.args)
            self.ranking = zip(fitness, self.stable)
            self.ranking.sort(reverse=True)
            # top ranking
            #current_ranking = [_[0] for _ in self.ranking[:20]]
            #if current_ranking != ranking:
            #    print "%6d [%s]" % ( self.generation, ' '.join('%.3f' % _ for _ in current_ranking))
            #ranking = current_ranking
            self.evaluation(self.ranking, self.random, self.args)
            self.stable = self.breader(self.ranking, self.random, self.args)
            self.generation += 1
#        self.random_state = self.random.state()
        return self.ranking

def run(args, trail):
    def generator(random, args):
        return Critter.create(random)
    def fitness(candidates, rand, args):
        check = Fitness(trail, args)
        return [check(_) for _ in candidates]
    def evaluation(fitness_chromo, rand, args):
        fitness, chromo = fitness_chromo[0]
        fitness, steps = fitness
        if fitness >= len(trail):
            raise StopIteration(chromo)

    breeder = Breeder(generator, args)
    camp = BreedingCamp(generator=generator,
                        fitness=fitness,
                        evaluation=evaluation,
                        breader=breeder,
                        random=Random(),
                        args=args)
    try:
        ranking = camp.evolve()
    except StopIteration:
        return True, camp
    return False, camp

def record(name, loops, args, trail):
    cur = get_db()
    for n in xrange(loops):
        success, camp = run(args, trail)
        sys.stdout.write('+' if success else '.')
        fitness, chromo = camp.ranking[0]
        fitness, steps = fitness
        params = (name, fitness, (1 if success else 0), steps,
                  camp.generation, args['population-size'],
                  dumps(camp, args, trail))
        print n, params[:-1]
        cur.execute("INSERT INTO results(name,fitness,found,steps,gen,pop,info) "
                    "VALUES(?, ?, ?, ?, ?, ?, ?)", params)
        cur.connection.commit()
    cur.connection.close()

def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', type=int, default=1, help='How many runs')
    parser.add_argument('-v', help='verbose', action='store_true')
    return parser.parse_args()


default_trail ={(0,1),(0,2),(0,3),(0,4),(0,5),(1,6),(2,7),(3,9), (4,11),
        (4,12), (6,12), (9, 11), (9, 9), (8,8), (9, 7), (10, 6)}

def get_db():
    conn = sqlite3.dbapi2.connect('results.sqlt')
    cursor = conn.cursor()
    return cursor

if __name__ == "__main__":
    import os.path
    parser = argparse.ArgumentParser()
    parser.add_argument('--gen', type=int, default=GENERATIONS_MAX,
                        help='Maximum generations')
    parser.add_argument('--pop', type=int, default=POPULATION_SIZE,
                        help='Population size per generation')
    parser.add_argument('--steps', type=int, default=TERMINATE_STEPS,
                        help='Max steps before fitness quits')
    parser.add_argument('--promote', type=float, default=BREED_PROMOTE,
                        help='%% of top ranked population to keep')
    parser.add_argument('--cross', type=float, default=BREED_CROSS,
                        help='%% of next gen by cross bread top ranked')
    parser.add_argument('--mutate', type=float, default=BREED_MUTATE,
                        help='%% of top ranked population to mutate')
    parser.add_argument('--rate', type=float, default=MUTATE_RATE,
                        help='Probability of changing a input state')
    parser.add_argument('--action', type=float, default=MUTATE_ACTION,
                        help='Probability of changing a state\'s action')
    parser.add_argument('--state', type=float, default=MUTATE_STATE,
                        help='Probability of changing a state\'s next state')
    parser.add_argument('--sample', action='store_true')
    parser.add_argument('--name', help='save to database under name')

    args = parser.parse_args()
    if not os.path.exists('results.sqlt'):
        cur = get_db()
        cur.execute("""CREATE TABLE results(
                    id INTEGER PRIMARY KEY,
                    name text,
                    fitness float,
                    found integer,
                    steps integer,
                    gen integer,
                    pop integer,
                    info text);""")
        cur.connection.commit()
    if args.sample:
        args = {'generations-max': args.gen,
                'population-size': args.pop,
                'terminate-steps': args.steps,
                'breed-promote': args.promote,
                'breed-cross': args.cross,
                'breed-mutate': args.mutate,
                'mutate-rate': args.rate,
                'mutate-action': args.action,
                'mutate-state': args.state
        }
        print args
        found, camp = run(args, default_trail)
        if found:
            print "Solution found"
        top = 2
        for ranking, chromo in zip(camp.ranking[:top], camp.stable[:top]):
            value = ranking[0][0]
            text = str(chromo).replace(' ','')
            print "{0:.2f}: {1}".format(value, text)
