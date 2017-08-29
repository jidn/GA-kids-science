import pdb
from random import Random
from bloodhound import Breeder, BreedingCamp, Critter, Fitness, \
    default_trail, arguments, run, record, dumps

NAME = 'cassie'

if __name__ == "__main__":
    cmdline = arguments()
    args = {
          # 'random-seed':0,
            'population-size': 10000,
            'terminate-steps':  70,
            'generations-max': 500,
            'breed-promote':    0.25,   # Promote top performers
            'breed-mutate':     0.25,   # Mutate from promoted
            'breed-cross':      0.25    # Cross breed from previous top population
    }
    if cmdline.n > 1:
        record(NAME, cmdline.n, args, default_trail)
    else:
        run(NAME, args, default_trail)
