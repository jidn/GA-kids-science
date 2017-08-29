import pdb
import pickle
from random import Random
from bloodhound import Breeder, BreedingCamp, Critter, Fitness, \
    default_trail, arguments, run, record, dumps

NAME = 'clinton'
if __name__ == "__main__":
    cmdline = arguments()
    args = {
          # 'random-seed':0,
            'population-size': 5000,
            'terminate-steps':  60,
            'generations-max': 1000,
            'breed-promote':    0.15,   # Promote top performers
            'breed-mutate':     0.15,   # Mutate from promoted
            'breed-cross':      0.5    # Cross breed from previous top population
    }
    if cmdline.n>1:
        record(NAME, cmdline.n, args, default_trail)
    else:
        run(NAME, args, default_trail)
