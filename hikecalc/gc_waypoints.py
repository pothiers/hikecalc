from geopy.distance import great_circle
import networkx as nx
import xml.etree.ElementTree as ET
import csv

# >>> newport_ri = (41.49008, -71.312796)
# >>> cleveland_oh = (41.499498, -81.695391)            # lat, lon
#
# available: feet,ft,kilometers,km,meters,m,mi,miles,nautical,nm
# >>> print(great_circle(newport_ri, cleveland_oh).miles)   
# 538.3904451566326


def read_waypoints(gpxfile):
    ns = dict(
        gpxx="http://www.garmin.com/xmlschemas/GpxExtensions/v3",
        gpx="http://www.topografix.com/GPX/1/1",
        gpsm="http.//www.gpsmaster.org/schema/gpsm/v1",
        gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1",
    )
    try:
        tree = ET.parse(gpxfile)
    except:
        print('ERROR: Ignoring file that could not be parsed: {}'
              .format(gpxfile.name))
        return set()
    
    root = tree.getroot()
    wpt_list = list()
    for wpt in root.findall(".//gpx:wpt",ns):
        wpt_list.append(dict(
            name = wpt.findtext('gpx:name',default='name-NA', namespaces=ns),
            cmt = wpt.findtext('gpx:cmt',default='cmt-NA', namespaces=ns),
            desc = wpt.findtext('gpx:desc',default='desc-NA', namespaces=ns),
            type = wpt.findtext('gpx:type',default='type-NA', namespaces=ns),
            lat = float(wpt.get('lat')),
            lon = float(wpt.get('lon'))
        ))
    return wpt_list
        
        
# waypoint (wp) defined by dict(lat,lon,name,cmt,desc,type)
# type: Campground, Mileage, POI, Rapid;   Mileage is IMPORTANT (used by name)
# Use graph to connect near other-waypoints. First to mileage, then to each other.
def near_river_mile(mileage_wps, other_wps, epsilon=.01):
    G = nx.Graph()
    nodes = [(wpt['name'],wpt) for wpt in (mileage_wps + other_wps)]
    G.add_nodes_from(nodes)
    # calc dist from each Mileage WP to all Other WPs that are within a mile of it.
    for mwp in mileage_wps:
        mloc = (mwp['lat'], mwp['lon'])
        mwp['rmile'] = int(mwp['cmt'])
        for owp in other_wps:
            dist = great_circle(mloc, (owp['lat'], owp['lon'])).miles
            if dist > 1.0 + epsilon:
                continue
            G.add_edge(mwp['name'], owp['name'], dist=dist)
    # Estimate river-mile of WPs by interpoloating between its two nearest Mileage WPs
    for owp in other_wps:
        adjdict = G[owp['name']]
        if len(adjdict) < 2:
            continue
        #!print('adjdict={}'.format(adjdict))
        (rm1, d1),(rm2,d2) = sorted([(k,v['dist']) for k,v in adjdict.items()],
                                    key=lambda p: p[1])[:2]
        print('(rm1, d1),(rm2,d2)={},{}'.format((rm1, d1),(rm2,d2)))
        if G.node[rm1]['rmile'] < G.node[rm2]['rmile']:
            rmile = G.node[rm1]['rmile'] + d1/(d1+d2)
        else:
            rmile = G.node[rm1]['rmile'] - d1/(d1+d2)
        owp['rmile'] = rmile
    return G

def partition_wpts(wpts):
    mileage = list()
    other = list()
    for wpt in wpts:
        if wpt.get('type') == 'Mileage':
            mileage.append(wpt)
        else:
            other.append(wpt)
    return mileage, other


def print_graph_nodes_as_csv(G, csvfilename):
    with open(csvfilename, 'w', newline='') as csvfile:
        fieldnames = ['rmile','name','cmt','desc','type','lat','lon']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for n,d in sorted(G.nodes_iter(data=True),
                          key=lambda p: p[1].get('rmile',999)):
            writer.writerow(d)
        

               
def gpx_waypoints_to_csv(gpxfile, csvfile):
    all_wpts = read_waypoints(gpxfile)
    mileage, other = partition_pts(all_wpts)
    G = near_river_mile(mileage, other)
    print_graph_nodes_as_csv(G)

    
