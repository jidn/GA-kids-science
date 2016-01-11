"""The fitness log returns a sequence of dicts with the following
state: current state tuple of (action, next_state)
action: current action from state
next_state: where I am going next from current state
pos: current cartesian position
exist: does sought item exist in front of me
looking: which direction am I looking
points: my current point

"""
import pickle
import pysvg.structure
import pysvg.builders
import pysvg.text
from bloodhound import get_db, default_trail, Fitness, TERMINATE_STEPS

def load_from_file(filename):
    r = open(filename, 'rt')
    data = pickle.loads(r.read())
    return data['chromo'], data['dlog']

class StateImage(object):
    """Use the current state information to create an image
    """
    def __init__(self, info, index):
        self.info = info
        self.log = info['log']
        self.trail = info['trail']
        self.index = index # which frame of log
        self.doc = pysvg.structure.Svg()
        self.g = pysvg.structure.G()
        self.svg = pysvg.builders.ShapeBuilder()
        self.t2p = self.svg.convertTupleArrayToPoints

        self.unit = 20.0

    def __call__(self):
        bound = self.get_bounding_rect()
        xmin, ymin, xmax, ymax = [self.unit * _ for _ in bound]
        o = (self.unit/2.0) + 1
        rect = self.svg.createRect(xmin-o, ymin-o,
                                   xmax-xmin+self.unit+o,
                                   ymax-ymin+self.unit+o,
                                   stroke='blue')
        self.g.addElement(rect)
        self.draw_trail()
        self.food()
        self.critter()

    def critter_rotate(self):
        moment = self.log[self.index]
        x = moment['looking'][0] - moment['pos'][0]
        y = moment['looking'][1] - moment['pos'][1]
        print moment['looking'], moment['pos']
        return x,y

    def critter2(self, moment):
        g = pysvg.structure.G()
        half = self.unit/2.0
        color
        obj = self.t2p([(-half, -half), (0, half), (half, -half)])
        obj = self.svg.createPolygon(obj, 1, 'red', 'red')
        g.addElement(obj)
        obj = self.svg.createRect(-half, -half,
                                  self.unit, half,
                                  stroke='red', fill='red')
        g.addElement(obj)
        return g

    def critter_arrow(self, moment):
        half = self.unit/2.0
        pnts = self.t2p([(-half, -half), (0, half), (half, -half)])
        return self.svg.createPolyline(pnts, strokewidth=2, stroke='red')
        #return self.svg.createPolygon(pnts, 1, 'red', 'red')

    def critter(self):
        "Draw the critter"
        moment = self.log[self.index]
        critter = self.critter_arrow(moment)
        #critter = self.critter2(moment)
        trans = pysvg.builders.TransformBuilder()
        rotate = {(0,1): 0,
                  (1,0): -90,
                  (0,-1): 180,
                  (-1,0): 90}[moment['looking']]
        if rotate:
            trans.setRotation(rotate)
        trans.setTranslation('{x},{y}'.format(
                    x=moment['pos'][0]*self.unit,
                    y=moment['pos'][1]*self.unit ))
        critter.set_transform(trans.getTransform())
        self.g.addElement(critter)

    def progress_bar(self):
        """Make progress bar
        """
        pass

    def food(self):
        "Draw remaining food"
        remaining = self.trail.copy()
        circ = self.svg.createCircle
        half = self.unit/2.0
        for idx in range(self.index):
            remaining.discard(self.log[idx]['pos'])
        for x, y in remaining:
            food = circ(x*self.unit, y*self.unit, self.unit/3.0,
                        1, 'green', 'white')
            self.g.addElement(food)

    def draw_trail(self):
        pnts = []
        half = self.unit/2.0
        for idx in range(self.index):
            x, y = self.log[idx]['pos']
            x *= self.unit
            y *= self.unit
            if not pnts or (x,y) != pnts[-1]:
                pnts.append((x,y))
        if pnts:
            line = self.svg.createPolyline(
                self.svg.convertTupleArrayToPoints(pnts))
            self.g.addElement(line)

    def write(self, filename):
        x1, y1, x2, y2 = self.get_bounding_rect()
        tx = self.unit * (abs(x1) + .5) + 1
        ty = self.unit * (abs(y1) + .5) + 1
        trans = pysvg.builders.TransformBuilder()
        trans.setTranslation('{x},{y}'.format(
            x=tx, y=ty))
        self.g.set_transform(trans.getTransform())
        self.doc.addElement(self.g)
        self.doc.save(filename)

    def get_bounding_rect(self):
        """The x1,y1 x2,y2 for the minimum bounding rectangle enclosing
        the critter's journey and trail.
        """
        xmin = 0
        xmax = 0
        ymin = 0
        ymax = 0

        for _ in self.log:
            xmin = min(xmin, _['pos'][0])
            xmax = max(xmax, _['pos'][0])
            ymin = min(ymin, _['pos'][1])
            ymax = max(ymax, _['pos'][1])

        for _ in self.trail:
            xmin = min(xmin, _[0])
            xmax = max(xmax, _[0])
            ymin = min(ymin, _[1])
            ymax = max(ymax, _[1])

        return xmin, ymin, xmax, ymax

def get_log(args):
    if args.name:
        r = open(args.name, 'rt')
        data = pickle.loads(r.read())
    elif args.id:
        cur = get_db()
        cur.execute("SELECT name, fitness, steps, info FROM results WHERE id=?",
                    (args.id,))
        name, fitness, steps, info = cur.fetchone()
        data = pickle.loads(info)
        data['steps'] = steps
        data['fitness'] = fitness
        data['name'] = name
        data['outfile'] = '{0[name]}{0[steps]}-id{1}.gif'.format(data, args.id)
    elif args.chromo:
        log = []
        chromo = eval(args.chromo)
        fitness = Fitness(default_trail, {'terminate-steps': args.steps})
        found, value = fitness(chromo, dlog=log)
        data = {'fitness': fitness,
                'outfile': 'anon.gif',
                'log': log,
                'trail': default_trail,
                'info': {'log': log, 'trail': default_trail},
        }
    else:
        raise RuntimeError("You must use --name or --id")
    return data

if __name__=="__main__":
    import sys
    import glob
    import os
    import subprocess
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', help='logfile')
    parser.add_argument('--id', type=int, help='database ID')
    parser.add_argument('--chromo', help='eval(input)')
    parser.add_argument('--steps', type=int, help='terminate-steps',
                        default=TERMINATE_STEPS)
    parser.add_argument('outfile', help='name of output file')
    args = parser.parse_args()

    data = get_log(args)
    # Delete sample*.svg sample*.gif
    for fl in glob.glob("sample*.*"):
        os.remove(fl)

    for frame in range(len(data['log'])):
        image = StateImage(data, frame)
        image()
        image.write('sample{0:03d}.svg'.format(frame))

    if args.outfile == '-':
        args.outfile = data['outfile']
    if not args.outfile.endswith('.gif'):
        args.outfile = '%s.gif' % args.outfile

    converting = ['convert', '-delay', '20', '-loop', '0',
                  'sample*.svg', args.outfile]
    subprocess.call(converting)
    for fl in glob.glob("sample*.*"):
        os.remove(fl)

