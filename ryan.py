import pdb
from random import Random
from bloodhound import Breeder, BreedingCamp, Critter, Fitness, \
    default_trail, arguments, run, record, dumps

NAME = 'ryan'

if __name__ == "__main__":
    cmdline = arguments()
    args = {
          # 'random-seed':0,
            'population-size': 1000,
            'terminate-steps':  100,
            'generations-max': 5000,
            'breed-promote':    0.3,   # Promote top performers
            'breed-mutate':     0.2,   # Mutate from promoted
            'breed-cross':      0.4    # Cross breed from previous top population
    }
    if cmdline.n > 1:
        record(NAME, cmdline.n, args, default_trail)
    else:
        run(NAME, args, default_trail)
