#! /usr/bin/env python
"""\

Command Line Interpreter for Hike Calculator.  This is user-friendly
way to access HC.  Easier implementation and installation than using
webservice.  Easier for users than free-form use via many invocations
of the HC with different options.

"""


import sys
import argparse
import logging
import subprocess
import cmd
import readline
import os.path
import shutil
import socket
from pathlib import PurePath

from . import hike_calc as hc

class HikecalcCli(cmd.Cmd):
    "Command Line Interpreter for Hike Calculator"
    intro = ('Welcome to the Hike Calculating Tool.'
             '   Type help or ? to list commands .\n')
    prompt = '(hc) '

    hiker = hc.Hiker()

    def parse_waypoints(self, arg):
        """Parse space delimited list of waypoints.  Each WP of form:
        wpname[.camp...] """
        wps = arg.split()
        camps = dict([(wp.split('.')[0], wp.split('.')[1:]) for wp in wps])
        waypoints = [wp.split('.')[0] for wp in wps]
        return waypoints, camps

    ############################################################################
    ### ----- HikeCalc commands --------
    def do_load(self, arg):
        """\
Load datafile.
SYNTAX: load filename
EXAMPLE:
    load ~/hikecalc/data/catalina.dat
"""
        filename = os.path.expanduser(arg)
        try:
            self.hiker.loadData(open(filename), 'path')
            self.hiker.appendTrailHeadsByPattern()
        except Exception as err:
            print('File not loaded')
            print(err)
        else:
            print('File loaded. Use "wp" to get list of waypoints.')
    def do_shortest(self, arg):
        """\
Display shortest route that passes through list of waypoints.
SYNTAX: shortest wpname[.camp1...] ...
EXAMPLE:
    load ~/hikecalc/data/catalina.dat
    shortest SabinoTH HutchsPool
"""
        
        waypoints,camps = self.parse_waypoints(arg)
        hc.shortest(self.hiker, waypoints, camps=camps, verbose=True)
    def do_th(self, arg):
        """\
Display names of all loaded trail-heads.
SYNTAX: th
"""
        names = sorted(self.hiker.trailheads)
        print('Trail-heads:\n  {}'.format('\n  '.join(names)))
    def do_wp(self, arg):
        """\
Display names of all loaded waypoints.
SYNTAX: wp
"""
        names = sorted(self.hiker.graph.nodes())
        print('Waypoints:\n  {}'.format('\n  '.join(names)))
    def do_dist(self, arg):
        """\
Display table of distances between all waypoint pairs connected by at
least one segment.
SYNTAX: dist [CSV_filename]
        """
        hc.genTable(self.hiker, None, csvfile=arg)
    def do_quit(self, arg):
        """Stop futzing with hike planning and exit"""
        print('Exiting Hike Calculating Tool')
        return True
    do_EOF = do_quit
    ###
    ############################################################################

def parse_nv(pair_list):
    'List name/value pairs ["n1=v1", "n2=v2"] to dict.'
    return dict([p.split('=') for p in pair_list])

def start_workflow():
    """The work-horse function."""
    HikecalcCli().cmdloop()

    
##############################################################################

def main():
    "Parse command line arguments and do the work."
    #!print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='HikeCalc Command Line Interpreter',
        epilog='EXAMPLE: %(prog)s"'
        )
    parser.add_argument('--version', action='version', version='1.0.1')
    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG'],
                        default='WARNING')
    args = parser.parse_args()

    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M')
    logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

    start_workflow()

if __name__ == '__main__':
    main()

    
