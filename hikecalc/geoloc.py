#! /usr/bin/env python
## @package pyexample
#  Documentation for this module. (for DOXYGEN)
#
#  More details.

'''\
<<Python script callable from command line.  Put description here.>>
'''

import os, sys, string, argparse, logging
import csv
from geopy.geocoders import Nominatim
import xml.etree.ElementTree as ET

## DOXYGEN documentation for a function.
#
# More details.
def get_adr(lat,lon):
    geolocator = Nominatim()
    locations = geolocator.reverse('{}, {}'.format(lat,lon), exactly_one=False)
    #!@for loc in locations:
    #!@    print(loc.address)
    # locations =>
    #   [Location(Douglas Spring, Tucson, Pima County, Arizona, United States of America, (32.227485, -110.6377209, 0.0))]
    # [l.address for l in location] =>
    #   ['Douglas Spring, Tucson, Pima County, Arizona, United States of America']
    return locations

def get_segment_addresses(gpxfile):
    ns = dict(
        gpx="http://www.topografix.com/GPX/1/1",
        gpxx="http://www.garmin.com/xmlschemas/GpxExtensions/v3",
        gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1",
        xsi="http://www.w3.org/2001/XMLSchema-instance",
        )
        
    tree = ET.parse(gpxfile)
    root = tree.getroot()
    #!print('tag={}, attrib={}'.format(root.tag, root.attrib))
    for trk in root.findall(".//gpx:trk",ns):
        name = trk.find('gpx:name',ns).text
        point = trk.find('gpx:trkseg/gpx:trkpt[1]',ns)
        print('Name={}, lat={}, lon={}'
              .format(name, point.get('lat'), point.get('lon')))
        locations = get_adr(point.get('lat'), point.get('lon'))
        print('Addresses ({}): {}'
              .format(len(locations),
                      '\t\n'.join([l.address for l in locations])
                  ))
        

##############################################################################

def main_tt():
    cmd = 'MyProgram.py foo1 foo2'
    sys.argv = cmd.split()
    res = main()
    return res

def main():
    #!    print('EXECUTING: {}\n\n'.format(' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        #!version='1.0.1',
        description='My shiny new python program',
        epilog='EXAMPLE: %(prog)s a b"'
    )
    parser.add_argument('infile',  help='GPX file containing "trkseg" element(s)',
                        type=argparse.FileType('r') )
    #!parser.add_argument('outfile', help='Output output',
    #!                    type=argparse.FileType('w') )
    parser.add_argument('--lat', help='Latitude (decimal)', type=float)
    parser.add_argument('--lon', help='Longitude (decimal)', type=float)
    parser.add_argument('--loglevel',      help='Kind of diagnostic output',
                        choices = ['CRTICAL','ERROR','WARNING','INFO','DEBUG'],
                        default='WARNING',
                        )
    args = parser.parse_args()
    #!args.outfile.close()
    #!args.outfile = args.outfile.name

    #!print 'My args=',args
    #!print 'infile=',args.infile


    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel) 
    logging.basicConfig(level = log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M'
                        )
    logging.debug('Debug output is enabled!!!')


    #get_adr(args.lat, args.lon)
    get_segment_addresses(args.infile)

if __name__ == '__main__':
    main()
