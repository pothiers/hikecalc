#! /usr/bin/env python
# see: catalina.edglist
# see: ~/src/python/hike-routing.org

'''
TODO:
  - validate node names against list of waypoints (from KML or GPX)


EXAMPLE:
ipython --pylab --no-color-info --classic
import hike_calc as hc
h = hc.tt()
# h.distanceHtmlTable("dist.html")
h.distanceHtmlTable("dist.html",waypoints=h.trailheads)
h.distanceStr("SabinoTH,BoxCampTH") # => 13.4
plt.savefig("catalina-dist.png")

'''

import os, sys, string, argparse, logging
import sys,itertools
from pprint import pprint
import difflib
from xml.etree.ElementTree import ElementTree
import re
import collections

import collections
import networkx.drawing
import networkx as nx
import networkx.algorithms.isomorphism.isomorphvf2 as vf2
from decimal import *

mileContext = Context(prec=1, rounding=ROUND_HALF_DOWN, 
                      Emin=0, Emax=9999)

# G=nx.Graph()
# hc.pathsToGraph('sabino.txt',G)
# gm = hc.DistGraphMatcher(h.graph,G)
# isos = [i for i in gm.subgraph_isomorphisms_iter()]
#  An iso maps node names from h.graph to G
class DistGraphMatcher(vf2.GraphMatcher):
    def semantic_feasibility(self, G1_node, G2_node):
        '''True if G1_node and G2_node have same "dist" edges values.
        G1 can have extra edges (ignored)'''
        G1_dist=sorted([d['dist']
                        for (u,v,d) in self.G1.edges([G1_node],data=True)])
        G2_dist=sorted([d['dist']
                        for (u,v,d) in self.G2.edges([G2_node],data=True)])

        # It would be better to use difflib to compare these sequences!!!
        # That would allow us to require duplicates (and allow slop in value).
        return (set(G2_dist).issubset(G1_dist))

# load
def pathsToGraph(data_file, GRAPH):
    '''G=nx.Graph()
hc.pathsToGraph("sabino.txt",G)

Data file can contain e.g.: 
  SabinoTH="Sabino Visitor Center" 0.8 PhoneLineTH
String is removed from token stream but saved in association with WP in a LUT.
'''
    nameLUT = dict() # nameLut[wp] = longName
    elevLUT = dict() # nameLut[wp] = elevation

    # match everything inside parens '()'
    #!name_re = re.compile(r'.+?(\w+)="([\w\s]+)"', flags=re.DEBUG) 
    name_re = re.compile(r'.*?(\w+)="([\w\s]+)"') 

    # Read Paths
    f = data_file
    lines = []
    for l in f:
        logging.debug('line: {}'.format(l))
        # remove comments
        idx = l.find('#')
        if idx >= 0:
            l = l[:idx]

        # Save Long Names and remove them from tokens
        nukem = []
        for mo in name_re.finditer(l):
            nukem.append((mo.start(2)-2,mo.end(2)+1)) # include quotes, equal
            (wp,name) = mo.group(1,2)
            nameLUT[wp] = name
            #print 'longname MATCHED: %s:<%s>[%d,%d]'% (wp,name,mo.start(2),mo.end(2))
        nukem.reverse()
        for (start,end) in nukem:
            l = l[:start] + l[end:]
        if len(l) > 0:
            lines.append(l)
    tokens = ' '.join(lines).split()

    logging.debug('nameLUT={}'.format(nameLUT))

    # Insert in graph
    for tok in tokens:
        if not isFloat(tok):
            GRAPH.add_node(tok,long_name=nameLUT.get(tok,''))
    prevWP = tokens[0]
    for idx,tok in enumerate(tokens[1:]):
        logging.debug('PrevWP=%s  Tok=%s', prevWP,tok)
        if isFloat(tok):
            # add checks for mid trail duplicate node names!!!
            nextWP = tokens[idx+2]
            assert(prevWP != nextWP)
            logging.debug('wps(%s,%s) %f',prevWP,nextWP,float(tok))
            dist = float(tok)
            #dist = int(round(Decimal(tok),1))
            GRAPH.add_edge(prevWP,nextWP,dist=dist)
        else:
            prevWP = tok


# tuple for running total    
#!Runtup = collections.namedtuple('Runtup','name,seg,cumm,lname')

def graphDistance(graph,  waypoints, explain=False):
    '''Find the (shortest) distance of the path that connects
    given list of waypoints. Use explain=True to get distance
    breakdown'''
    total = 0
    path = []
    gn = graph.nodes()
    for (a,b) in zip(waypoints[:-1],waypoints[1:]):
        logging.debug('Calc shortest between: {}  and {}'.format(a,b))
        if nx.has_path(graph, a, b):
            seg = nx.shortest_path_length(graph,a,b,'dist')
            path.extend(nx.shortest_path(graph,a,b,'dist'))
        else:
            seg = float('+inf') # Decimal('Infinity')
        total += seg
        logging.debug('seg=%.1f total=%.1f From %s to %s',seg,total,a,b)
        logging.debug('  path={}'.format(path))
    running = [] # [runtup, ...]
    if explain:
        cum = 0
        for idx in range(len(path)-1):
            if path[idx] == path[idx+1]: continue
            segdist = graph[path[idx]][path[idx+1]]['dist']
            cum += segdist
            lname = graph.node[path[idx+1]]['long_name']
            running.append((path[idx+1], segdist, cum, lname))
            logging.debug('{} miles: {} to {}'
                          .format(segdist, path[idx], path[idx+1]))
    return total,running


class Hiker(object):
    'Manages stuff for planning a hike'
    graph = nx.Graph()
    pathfile = None
    trailheads = []
    
    def __init__(self, graph=None):
        if graph:
            self.graph = graph
    

    def readKmlWaypoints(self,kmlfile):
        ns = '{http://www.opengis.net/kml/2.2}'
        tree = ElementTree()
        tree.parse("/home/pothiers/src/python/waypoints.kml")
        wayPoints = [e.text for e
                     in tree.findall('.//{0}Placemark/{0}name'.format(ns))]
        return wayPoints

    #infile = '/home/pothiers/src/python/catalina-edges.txt'
#!    def readTrails(self,infile):
#!        f = open(infile)
#!        lines = [l.strip() for l in f.readlines() if l[0] != '#']
#!        tokens = ' '.join(lines).split()
#!        f.close()
#!        return tokens
#!
#!    def trailsToGraph(self,trails):
#!        prevWP = trails[0]
#!        for idx,tok in enumerate(trails[1:]):
#!            print 'PrevWP=%s  Tok=%s' % (prevWP,tok)
#!            if isFloat(tok):
#!                # add checks for mid trail duplicate node names!!!
#!                nextWP = trails[idx+2]
#!                assert(prevWP != nextWP)
#!                print 'wps(%s,%s) %f'% (prevWP,nextWP,float(tok))
#!                self.graph.add_edge(prevWP,nextWP,dist=float(tok))
#!            else:
#!                prevWP = tok
#!        return self.graph
#!    def importTrails(self,fname):
#!        tokens = self.readTrails(fname)
#!        self.trailsToGraph(tokens)


    def reloadPaths(self):
        self.loadPaths(self.pathfile)

    #fname = '/home/pothiers/src/python/catalina-edges.txt'
    def loadPaths(self, data_file, eraseOld=True, info=False):
        fname = data_file.name
        self.pathfile = fname
        if eraseOld:
            self.graph.clear()
        pathsToGraph(data_file, self.graph)
        if info:
            print('Graph info: \n{}'.format(nx.info(self.graph)))

    def appendTrailHeads(self,waypoints):
        self.trailheads.extend(waypoints)
        
    def appendTrailHeadsByPattern(self, regexp='.+TH'):
        self.trailheads.extend([n for n in self.graph.nodes_iter()
                                if re.match(regexp,n)])
                           
    def show(self,outfile=None):
        import matplotlib.pyplot as plt

        for u,v,d in self.graph.edges(data=True):
            d['weight'] = 1.0/(1+d['dist'])
        pos = nx.spring_layout(self.graph,weight='weight')
        elabels = dict([((u,v),d['dist'])
                        for (u,v,d) in self.graph.edges(data=True)])
        plt.clf()
        nx.draw(self.graph, pos=pos)
        nx.draw_networkx_edge_labels(self.graph, pos=pos, edge_labels=elabels)
        plt.show()
        if outfile:
            plt.savefig(outfile)

    # h.distanceStr('SabinoTH,BoxCampTH') # => 13.4
    def distanceStr(self,  waypointsStr, explain=False):
        return self.distance([n.strip() for n in waypointsStr.split(',')],
                             explain=explain)
                     

    # h.distance(['SabinoTH','BoxCampTH']) # => 13.4
    # h.distance(['SabinoTH','BoxCampTH'], explain=True)
    def distance(self,  waypoints, explain=False):
        return graphDistance(self.graph, waypoints, explain=explain)[0]
        #!'''Find the (shortest) distance of the path that connects
        #!given list of waypoints. Use explain=True to get distance
        #!breakdown'''
        #!total = 0
        #!#!!! Implement explain=True
        #!path = []
        #!for (a,b) in itertools.izip(waypoints[:-1],waypoints[1:]):
        #!    seg = nx.shortest_path_length(self.graph,a,b,'dist')
        #!    path.extend(nx.shortest_path(self.graph,a,b,'dist'))
        #!    total += seg
        #!    logging.debug('seg=%.1f total=%.1f From %s to %s',seg,total,a,b)
        #!if explain:
        #!    for idx in range(len(path)-1):
        #!        print '%3.1f miles: %s to %s' % (self.graph[path[idx]][path[idx+1]]['dist'],
        #!                                         path[idx],
        #!                                         path[idx+1])
        #!return total

    def calcDist(self,u,v,defaultValue):
        d = defaultValue
        try:
            d = nx.shortest_path_length(self.graph,u,v,'dist')
        except Exception:
            pass
        return d
        
    def distanceTable(self, waypoints=None):
        mat = dict() # mat[(n1,n2)] = dist
        wplist = self.graph.nodes() if (waypoints == None) else waypoints
        for (u,v) in itertools.product(wplist, repeat=2):
            mat[(u,v)] = self.calcDist(u,v,float('+inf'))
        return mat

    def distanceHtmlTable(self):
        #wplist = self.graph.nodes()
        html = ''
        count = 1
        for wplist in nx.connected_components(self.graph):
            print('DBG: connected_component #%d'%count)
            count += 1
            mat = self.distanceTable(wplist)
            html += '<TABLE border="1" cellspacing="0"><THEAD>'
            html +='<TR><TH>(minimum distance)</TH>'
            for iu,u in enumerate(sorted(wplist)):
                html +='<TH>%02d</TH>' % (iu,)
            html +='</TR></THEAD>'
            for iu,u in enumerate(sorted(wplist)):
                html +='<TR><TH align="left">%02d %s</TH>'% (iu,u)
                for v in sorted(wplist):
                    d = '%3.1f'%mat[(u,v)] if u != v else '  -  '
                    html +='<TD align="center">%s</TD>' % (d,)
                html +='</TR>'
            html +='</TABLE>'       
            html += '<br />'
        return html
            
    def findEnds(self, regexp='.*'):
        'Return nodes at end of paths (have only one edge)'
        return [n for n in self.graph
                if (len(self.graph.neighbors(n)) < 2) and re.match(regexp,n)
                ]   

    def findJunctions(self, regexp='.*'):
        'Return nodes at junctions (have more than 2 edges)'
        return [n for n in self.graph
                if (len(self.graph.neighbors(n)) > 2) and re.match(regexp,n)
                ]   

    def findTrans(self, regexp='.*'):
        '''Return nodes "in transit" (have exactly 2 edges). NB: A
        TrailHead for two trails would match this!'''
        return [n for n in self.graph
                if (len(self.graph.neighbors(n)) == 2) and re.match(regexp,n)
                ]   

    def longestPaths(self,regexp='.+TH',explain=False):
        maxd = 0
        longest = None
        for (start,end) in itertools.product(self.findEnds(regexp=regexp), repeat=2):
            if start == end: continue
            d = None
            try:
                d = self.distance([start,end])
                #!print 'DBG: dist %s to %s = %s'%(start,end,d)
            except Exception:
                continue
            if explain:
                print('%4.1f miles: %s to %s'%(d,start,end))
            if (d < 999999999) and (d > maxd):
                maxd = d
                longest = (start,end)
        return longest[0], longest[1], maxd

    def findAlternateRoutes(self, startWP, endWP):
        pass

    def colorDisjointSubgraphs(self):
        pass


def test():
    pprint(G.edges(data=True))
    #print(nx.dijkstra_path(G,'fingerTH','ventanaTH'))
    print((nx.shortest_path(G,'fingerTH','ventanaTH','dist')))
    print((nx.shortest_path_length(G,'fingerTH','ventanaTH','dist'))) # ==> 12.0

    # add distance loop
    nx.shortest_path_length(G,'bearTH','sabinoTH','dist')+nx.shortest_path_length(G,'bearTH','jpalisade','dist')+nx.shortest_path_length(G,'sabinoTH','jpalisade','dist')
    #nx.draw(G)


def distance(G, *waypoints):
    total = 0
    for (a,b) in zip(waypoints[:-1],waypoints[1:]):
        seg = nx.shortest_path_length(G,a,b,'dist')
        total += seg
        print('seg=%.1f total=%.1f From %s to %s' % (seg,total,a,b))
    return total
    
def OLDreadKmlWaypoints(G, kmlfile):
    tree = xml.ElementTree()
    tree.parse("/home/pothiers/src/python/waypoints.kml")
    #placemarks=tree.findall('.//{http://www.opengis.net/kml/2.2}Placemark')
    #wpName = placemarks[0].find('{http://www.opengis.net/kml/2.2}name').text
    wpNames = [e.text for e in tree.findall('.//{http://www.opengis.net/kml/2.2}Placemark/{http://www.opengis.net/kml/2.2}name')]
    lut = dict(list(zip(wpNames,list(range(len(wpNames))))))
    lutInv = dict(list(zip(list(lut.values()),list(lut.keys()))))

def isFloat(string):
    try:
        f = float(string)
    except Exception:
        return False
    return True

def trailsToGraph(trails):
    G = nx.Graph()
    prevWP = trails[0]
    for idx,tok in enumerate(trails[1:]):
        print('PrevWP=%s  Tok=%s' % (prevWP,tok))
        if isFloat(tok):
            # add checks for mid trail duplicate node names!!!
            nextWP = trails[idx+2]
            assert(prevWP != nextWP)
            print('wps(%s,%s) %f'% (prevWP,nextWP,float(tok)))
            G.add_edge(prevWP,nextWP,dist=float(tok))
        else:
            prevWP = tok
    return G

    

def tt():
    h = Hiker()
    #!placemarks = set(h.readKmlWaypoints('/home/pothiers/src/python/waypoints.kml'))
    #!pprint(placemarks)
    #!G=nx.read_edgelist('/home/pothiers/src/python/catalina.edglist',
    #!                   data=(('dist',float)
    #!                         ,('name',str)),
    #!                   nodetype=str)
    #!pprint(G.edges(data=True))
    
    #!trailFile = '/home/pothiers/src/python/catalina-edges.txt'
    #!tokens = h.readTrails(trailFile)
    #!print 'tokens=',tokens
    #!G=trailsToGraph(tokens)
    #!nx.write_edgelist(G,'foo.edgelist')
    #!
    #!
    #!waypoints = set(G.nodes())
    #!
    #!diff1 = sorted(list(placemarks.difference(waypoints)))
    #!diff2 = sorted(list(waypoints.difference(placemarks)))
    #!
    #!print 'placemarks-waypoints: ',' '.join(diff1)
    #!print 'waypoints-placemarks: ',' '.join(diff2)
    #!
    #!d = difflib.Differ()
    #!result = list(d.compare([(s+'\n') for s in sorted(waypoints)],
    #!                        [(s+'\n') for s in sorted(placemarks)]))
    #!print "Waypoints -> Placemarks:"
    #!sys.stdout.writelines(result)
    #!
    #!print '#'*70
    #!result = list(d.compare([(s+'\n') for s in sorted(placemarks)],
    #!                        [(s+'\n') for s in sorted(waypoints)]  ))
    #!print "Placemarks -> Waypoints:"
    #!sys.stdout.writelines(result)
    #!
    #!
    #!print 'Still to add (to %s):'%trailFile
    #!print ' '.join(diff1)

    #h.importTrails('/home/pothiers/src/python/catalina-edges.txt')
    h.loadPaths('/home/pothiers/sandbox/hike_calculator_site/hike_calc/annotated-paths.txt')
    h.appendTrailHeadsByPattern()
    h.show() #  If python started like: ipython -pylab

    print('Longest path in DB (TH to TH): (%s to %s) = %.1f miles'%h.longestPaths())

    return h

def tt_1():
    h = Hiker()
    h.loadPaths('/home/pothiers/sandbox/hike_calculator_site/hike_calc/annotated-paths.txt')
    h.appendTrailHeadsByPattern()
    wps_str = 'MarshallGulchTH,MtKimbleJct,MudSpring,MarshallGulchTH'
    print(('Distances for: %s:\n%s'
           %(wps_str,
             h.distance(wps_str.split(','), explain=True))))

def genTable(hiker, args):
    #!h = Hiker()
    #!h.loadPaths(dist_data_file)
    #!h.appendTrailHeadsByPattern()

    mat = hiker.distanceTable()
    #! print('Distance table: {}'.format(mat))
    for ((n1, n2),dist) in mat.items():
        print('{}, \t{}, \t{}'.format(n1, n2, dist))
    
   #! wps_str = 'MarshallGulchTH,MtKimbleJct,MudSpring,MarshallGulchTH'
   #! print(('Distances for: %s:\n%s'
   #!        %(wps_str,
   #!          h.distance(wps_str.split(','), explain=True))))
    

def infoShortest(hiker, args):
    logging.debug('infoShortest using THs ({}): '.format(args.waypoints))

    missing = set(args.waypoints) - set(hiker.graph.nodes())
    if 0 != len(missing):
        print('The waypoints: {} are not in the data-set.'.format(missing))
        infoWaypoints(hiker)
        sys.exit(1)
    total, running = graphDistance(hiker.graph, args.waypoints, explain=True)
    if args.cummulative:
        details = '\n  '.join(['{:>5.1f}  {}'.format(cdist,wp)
                               for (wp, d1, cdist, d2) in running])
    else:
        details = ', '.join([wp for (wp,segdist, cumdist, lname) in running])
    print('Shortest distance from "{}" to "{}" is {:.1f} miles via:\n  {}'
          .format(
              running[0][0],
              running[-1][0],
              total,
              details
          ))
                
def infoTrailheads(hiker, args):
    print('Trail-heads: {}'.format(', '.join(hiker.trailheads)))

def infoWaypoints(hiker):
    print('Waypoints: {}'.format(', '.join(hiker.graph.nodes())))
    
##############################################################################


def main():
    #!print('EXECUTING: {}\n\n'.format(' '.join(sys.argv)))
    #!description='My shiny new python program',
    #!epilog='EXAMPLE: %(prog)s a b"'

    parser = argparse.ArgumentParser('hc')
    subparsers = parser.add_subparsers(title='subcommands',
                                       help='sub-command help')

    parser.add_argument('--loglevel',      help='Kind of diagnostic output',
                        choices = ['CRTICAL', 'ERROR', 'WARNING',
                                   'INFO', 'DEBUG'],
                        default='WARNING',
                        )
    parser.add_argument('infile',  help='Input file',
                        type=argparse.FileType('r') )


    pars_t = subparsers.add_parser('table',
                help=('Output table of distances. '
                      'Distance between every pair of waypoints that are '
                      'connected by a path of 1 or more segments.'
                  ))
    pars_t.add_argument('-f', '--format',
                        choices = ['csv', 'txt'],
                        default='csv',
                        help='Output format',
                        )
    pars_t.set_defaults(func=genTable)


    pars_h = subparsers.add_parser('th',
                                   help='Output all trail-heads')
    pars_h.set_defaults(func=infoTrailheads)
    
    pars_s = subparsers.add_parser('shortest',
                                   help='Find shortest route')
    pars_s.add_argument('-w', '--waypoints', 
                        action='append',
                        help='List of waypoints to consider. (multi allowed)')
    pars_s.add_argument('--cummulative', 
                        action='store_true',
                        help='List cummulative distance)')
    pars_s.set_defaults(func=infoShortest)


    args = parser.parse_args()


    ########################################
    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel) 
    logging.basicConfig(level = log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M'
                        )
    logging.debug('Debug output is enabled!!!')
    logging.debug('args={}'.format(args))
    ########################################

    hiker = Hiker()
    hiker.loadPaths(args.infile)
    hiker.appendTrailHeadsByPattern()

    args.func(hiker, args)
    
    #!elif args.cmd == 'trailheads':
    #!    print('Trailheads: {}'.format(', '.join(h.trailheads)))
    

if __name__ == '__main__':
    main()
