#! /usr/bin/env python3
'''\
Get addresses for a GPX segment.
'''
import sys, argparse, logging
from geopy.geocoders import Nominatim
import xml.etree.ElementTree as ET

## DOXYGEN documentation for a function.
#
# More details.
def get_adr(lat,lon):
    geolocator = Nominatim()
    locations = geolocator.reverse('{}, {}'.format(lat,lon), exactly_one=True)
    #!@for loc in locations:
    #!@    print(loc.address)
    # locations =>
    #   [Location(Douglas Spring, Tucson, Pima County, Arizona, United States of America, (32.227485, -110.6377209, 0.0))]
    # [l.address for l in location] =>
    #   ['Douglas Spring, Tucson, Pima County, Arizona, United States of America']
    return locations

def get_segment_addresses(gpxfile, verbose=True):
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
    addresses = set()
    for trk in root.findall(".//gpx:trk",ns):
        name_elem = trk.find('gpx:name',ns)
        name = 'NO-NAME' if name_elem == None else  name_elem.text
        point = trk.find('gpx:trkseg/gpx:trkpt[1]',ns)
        locations = get_adr(point.get('lat'), point.get('lon'))
        addresses.add(locations.address)

        if verbose:
            print('File: {}'
                  '\n\t Track Name: \t{}'
                  '\n\t Lat/Lon:    \t{},{}'
                  '\n\t Address:    \t{}'
                  .format(gpxfile.name,
                          name,
                          point.get('lat'), point.get('lon'),
                          locations.address,
                          ))
    return addresses
        

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
    parser.add_argument('gpxfiles',
                        nargs='+',
                        help='GPX file(s) containing "trkseg" element(s)',
                        type=argparse.FileType('r') )
    #!parser.add_argument('outfile', help='Output output',
    #!                    type=argparse.FileType('w') )
    parser.add_argument('--lat', help='Latitude (decimal)', type=float)
    parser.add_argument('--lon', help='Longitude (decimal)', type=float)
    parser.add_argument('--quiet', action='store_true', help='Less output)')
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
    adrs = set()
    for gpxfile in args.gpxfiles:
        if args.quiet:
            new = get_segment_addresses(gpxfile, verbose=False)
        else:
            new = get_segment_addresses(gpxfile)
        adrs.update(new)
        
    print('Unique address found in files: {}'
          .format('\n\t '.join(sorted(list(adrs)))))


if __name__ == '__main__':
    main()
