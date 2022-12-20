#! /usr/bin/env python
# see: catalina.edglist
# see: ~/src/python/hike-routing.org

'''
TODO:
  - validate node names against list of waypoints (from KML or GPX)


EXAMPLE:
hikecalc/hike_calc.py shortest -w SabinoTH -w TheWindow ~/sandbox/hikecalc/data/catalina.dat

sqlite3  grand-canyon.db < hikecalc/graph_schema.sql
hc --format csv -n data/tonto-west.lut.csv --db grand-canyon.db shortest -w Indian_Garden -w Granite_Rapids -w Hermit_Rest_via_Hermit_Trail data/tonto-west.csv

hc --format csv -n data/tonto-west.lut.csv shortest -w Indian_Garden -w Hermit_Rest_via_Hermit_Trail data/tonto-west.csv

hc --loglevel=DEBUG --format csv -n data/tonto-west.lut.csv shortest -w x1 -w x4 data/tonto-west.csv

hc --format csv wp  data/tonto-west.csv

ipython --pylab --no-color-info --classic
import hike_calc as hc
h = hc.tt()
# h.distanceHtmlTable("dist.html")
h.distanceHtmlTable("dist.html",waypoints=h.trailheads)
h.distanceStr("SabinoTH,BoxCampTH") # => 13.4
plt.savefig("catalina-dist.png")

'''

import sys, argparse, logging
import itertools
from pprint import pprint
#!import difflib
from xml.etree.ElementTree import ElementTree
import re
import csv
import sqlite3
import yaml
import os.path
#!import datetime

#!import collections
#!import networkx.drawing
import networkx as nx
import networkx.algorithms.isomorphism.isomorphvf2 as vf2
#from decimal import *

#mileContext = Context(prec=1, rounding=ROUND_HALF_DOWN,  Emin=0, Emax=9999)



def save_graph(G, dbfile):
    con = sqlite3.connect(dbfile)
    cur = con.cursor()
    nodes = [(n, d.get('shortname','NULL'), d.get('longname','NULL'))
             for n,d in G.nodes_iter(data=True)]
    cur.executemany('insert into node values (?,?,?)',nodes)
    edges = [(u, v, d['dist'])
             for u,v,d in G.edges_iter(data=True)]
    cur.executemany('insert into edge values (?,?,?)',edges)
    con.commit()
    con.close()


def csv_to_graph(csv_adj_file, G, csv_lut_file=None):
    '''Add nodes and edges to graph using data from CSV file(s).

csv_adj_file :: Adjacency matrix.  Row/column headers except 80,0) are
  IDs. Top/Left (0,0) is edge attribute name.  Cells are
  attribute value.

csv_lut_file :: Maps ID to NAME.  Nodes in graph take NAME, or ID if
    there is not ID in the LUT.
    '''
    lut = dict() # lut[id] => name
    if csv_lut_file:
        with open(csv_lut_file) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                lut[row['ID']] = row['NAME']

    with open(csv_adj_file) as csvfile:
        reader = csv.DictReader(csvfile)
        id1_fld = reader.fieldnames[0]
        id_list = reader.fieldnames[1:]
        adj_name = reader.fieldnames[0]
        for id in id_list:
            # Use ID for node name if its not in LUT
            G.add_node(lut.get(id,id))

        for row in reader:
            id1 = row[id1_fld]
            node1 = lut.get(id1, id1)
            for id2 in id_list:
                node2 = lut.get(id2, id2)
                edict = {adj_name : float(row[id2])}
                logging.debug('edge ({}, {}) dict: {}'
                              .format(node1, node2, edict))
                G.add_edge(node1, node2, attr_dict=edict)



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


def yamlToGraph(yaml_data_file, GRAPH):
    yd = yaml.safe_load(yaml_data_file)
    return yd

# load
def pathsToGraph(data_file, GRAPH):
    '''
data_file:: open file (not filename)
G=nx.Graph()
hc.pathsToGraph("sabino.txt",G)

Data file can contain e.g.:
  SabinoTH="Sabino Visitor Center" 0.8 PhoneLineTH
String is removed from token stream but saved in association with WP in a LUT.
'''
    nameLUT = dict() # nameLut[wp] = longName
    #!elevLUT = dict() # nameLut[wp] = elevation

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

def graphDistance(graph,  waypoints, camps=None, explain=False):
    '''Find the (shortest) distance of the path that connects
    given list of waypoints. Use explain=True to get distance
    breakdown'''
    total = 0
    path = []
    #! gn = graph.nodes()
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

    if explain:
        if not camps:
            camps = dict()

        #!lname = graph.node[path[0]].get('long_name',path[0])
        lname = graph.nodes[path[0]].get('long_name',path[0])
        running = [(path[0], 0, 0, 0, lname, 'Start')] # [runtup, ...]
        dcum = 0
        tcum = 0
        for idx in range(len(path)-1):
            if path[idx] == path[idx+1]: continue
            segdist = graph[path[idx]][path[idx+1]]['dist']
            dcum += segdist
            tcum += segdist
            #!lname = graph.node[path[idx+1]].get('long_name',path[idx+1])
            lname = graph.nodes[path[idx+1]].get('long_name',path[idx+1])
            comment = camps.get(path[idx+1],'Camp') if path[idx+1] in camps else ''
            if idx == range(len(path)-1)[-1]:
                comment = 'Done'
            running.append((path[idx+1], segdist, dcum, tcum, lname, comment))
            if path[idx+1] in camps:
                dcum = 0
                running.append(('---------', 0, 0, tcum, lname, '----------'))
                #!running.append((path[idx+1], 0, 0, tcum, lname, 'Day Start'))
            logging.debug('{} miles: {} to {}'
                          .format(segdist, path[idx], path[idx+1]))
    # running :: [(wp, segDist, dayCumDist, tripCumDist, longName, comment),...]
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

    def loadData(self, data_file, fname, format,
                 names=None, eraseOld=True, info=False):
        #fname = data_file.name
        self.pathfile = fname

        if eraseOld:
            self.graph.clear()

        if format == 'path':
            pathsToGraph(data_file, self.graph)
        elif format == 'csv':
            data_file.close()
            fname = data_file.name
            csv_to_graph(fname, self.graph, csv_lut_file=names)
        elif format == 'yaml':
            yd = yaml.safe_load(data_file)
            print('yd={}'.format(yd))
        else:
            logging.error('Unknown data file format ("{}"} requested.'
                          .format(format))
            sys.exit(1)

        if info:
            print('Graph info: \n{}'.format(nx.info(self.graph)))

    def appendTrailHeads(self,waypoints):
        self.trailheads.extend(waypoints)

    def appendTrailHeadsByPattern(self, regexp='.+TH'):
        #self.trailheads.extend([n for n in self.graph.nodes_iter()
        self.trailheads.extend([n for n in self.graph
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


def test(G):
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
    import xml.etree
    tree = xml.etree.ElementTree()
    tree.parse("/home/pothiers/src/python/waypoints.kml")
    #placemarks=tree.findall('.//{http://www.opengis.net/kml/2.2}Placemark')
    #wpName = placemarks[0].find('{http://www.opengis.net/kml/2.2}name').text
    #!wpNames = [e.text for e in tree.findall('.//{http://www.opengis.net/kml/2.2}Placemark/{http://www.opengis.net/kml/2.2}name')]
    #!lut = dict(list(zip(wpNames,list(range(len(wpNames))))))
    #!lutInv = dict(list(zip(list(lut.values()),list(lut.keys()))))

def isFloat(string):
    try:
        float(string)
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

def genTable(hiker, args, csvfile=None):
    #!h = Hiker()
    #!h.loadPaths(dist_data_file)
    #!h.appendTrailHeadsByPattern()

    mat = hiker.distanceTable()
    #! print('Distance table: {}'.format(mat))
    if csvfile == None:
        for ((n1, n2),dist) in mat.items():
            print('{}, \t{}, \t{}'.format(n1, n2, dist))
        return None
    with open(csvfile, 'w') as csv:
        for ((n1, n2),dist) in mat.items():
            if n1 == n2:
                continue
            print('{},{},{}'.format(n1, n2, dist), file=csv)


   #! wps_str = 'MarshallGulchTH,MtKimbleJct,MudSpring,MarshallGulchTH'
   #! print(('Distances for: %s:\n%s'
   #!        %(wps_str,
   #!          h.distance(wps_str.split(','), explain=True))))


def shortest(hiker, waypoints,
             #campwps=None, # [(wp,nightNum...), ...]
             camps=None, # dict[wp] => [nightLabel, ...]
             verbose=False):
    if camps == None:
        camps = dict()

    missing = set(waypoints) - set(hiker.graph.nodes())
    if 0 != len(missing):
        print('The waypoints: {} are not in the data-set.'.format(missing))
        infoWaypoints(hiker, None)
        sys.exit(1)
    total, running = graphDistance(hiker.graph, waypoints,
                                   camps=camps, explain=True)
    if verbose:
        details = '\n  '.join(['{:>5.1f} {:>5.1f} {:>5.1f} {:<25s}  {}'
                               .format(sdist, ddist, tdist, wp, rem)
                               for (wp, sdist, ddist, tdist, lname, rem)
                               in running])
    else:
        details = ', '.join([wp for (wp, *_) in running])
    print('The shortest distance from "{}" to "{}" is {:.1f} miles via:\n  {}'
          .format(waypoints[0], running[-1][0], total, details))

def infoShortest(hiker, args):
    if args.first_day:
        d,m,y = [int(n) for n in args.first_day.split('/')]
        #!firstday =  datetime.date(y,m,d)

    #!waypoints = args.waypoint
    if args.camp:
        #pfx = args.prefix_camp if args.prefix_camp else 'Night '
        pfx = args.prefix_camp if args.prefix_camp else ''
        camp_list = [(wp,pfx+','.join(nights)) for (wp,*nights) in args.camp]
        camps = dict(camp_list)
    else:
        camps = dict()
    logging.info('infoShortest using waypoints: {}, camps: {} '
                 .format(args.waypoint, camps.keys()))
    logging.info('camps={}'.format(camps))

    #! missing = set(waypoints) - set(hiker.graph.nodes())
    #! if 0 != len(missing):
    #!     print('The waypoints: {} are not in the data-set.'.format(missing))
    #!     infoWaypoints(hiker, args)
    #!     sys.exit(1)
    #! total, running = graphDistance(hiker.graph, waypoints,
    #!                                camps=camps, explain=True)
    #! if args.details:
    #!     details = '\n  '.join(['{:>5.1f} {:>5.1f} {:>5.1f} {:<25s}  {}'
    #!                            .format(sdist, ddist, tdist, wp, rem)
    #!                            for (wp, sdist, ddist, tdist, lname, rem)
    #!                            in running])
    #! else:
    #!     details = ', '.join([wp for (wp, *_) in running])
    #! print('The shortest distance from "{}" to "{}" is {:.1f} miles via:\n  {}'
    #!       .format(
    #!           waypoints[0],
    #!           running[-1][0],
    #!           total,
    #!           details
    #!       ))
    shortest(hiker, args.waypoint, camps=camps, verbose=args.details)

def infoTrailheads(hiker, args):
    print('Trail-heads:\n  {}'.format('\n  '.join(hiker.trailheads)))

def infoWaypoints(hiker, args):
    print('Waypoints:\n  {}'.format('\n  '.join(hiker.graph.nodes())))

##############################################################################


def main():
    #!print('EXECUTING: {}\n\n'.format(' '.join(sys.argv)))
    description='My shiny new python program',
    epilog='EXAMPLE: %(prog)s --help"'

    parser = argparse.ArgumentParser('hc')
    subparsers = parser.add_subparsers(title='subcommands',
                                       help='sub-command help')

    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices = ['CRTICAL', 'ERROR', 'WARNING',
                                   'INFO', 'DEBUG'],
                        default='WARNING',
                        )
    parser.add_argument('infile',
                        #type=argparse.FileType('r'),
                        help='Distance data filename'  )
    parser.add_argument('-f',  '--format',
                        help='Input file format',
                        default='path',
                        choices = ['csv', 'path'],
                        )
    parser.add_argument('-n', '--names', help='ID to Name mapping (csv)')
    parser.add_argument('--db', help='Insert graph in this DB')

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

    pars_w = subparsers.add_parser('wp',
                                   help='Output all waypoints')
    pars_w.set_defaults(func=infoWaypoints)

    pars_s = subparsers.add_parser('shortest',
                                   help='Find shortest route')
    pars_s.add_argument('-w', '--waypoint',
                        action='append',
                        help='Waypoint to include. (multi allowed)')
    pars_s.add_argument('-c', '--camp',
                        nargs=2,
                        action='append',
                        help=('(waypoint night-number) of camp. Reset '
                              'distance. (multi allowed)'))
    pars_s.add_argument('--details',
                        action='store_true',
                        help='List cummulative distance)')
    pars_s.add_argument('--prefix_camp',
                        default='',
                        help=('Prefix camp number with this string when '
                              'outputting details.'))
    pars_s.add_argument('--first_day',
                        help='Date (mm/dd/yyyy) of first day of hiking')
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
    #!hiker.loadPaths(args.infile)
    datafile = open(os.path.expanduser(args.infile), 'r')
    hiker.loadData(datafile, args.infile, args.format, names=args.names)
    if args.db:
        save_graph(hiker.graph, args.db)

    hiker.appendTrailHeadsByPattern()

    args.func(hiker, args)

    #!elif args.cmd == 'trailheads':
    #!    print('Trailheads: {}'.format(', '.join(h.trailheads)))


if __name__ == '__main__':
    main()
