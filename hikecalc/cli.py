#! /usr/bin/env python
"""\

Command Line Interpreter (CLI) for Hike Calculator. Balance between
full web app and multiple invocations of script. This is user-friendly
way to access HC.  Easier implementation and installation than using
webservice.  Easier for users than free-form use via many invocations
of the HC with different options.

The commands provided by the CLI should provide all the functionality
that is available via command line arguments of hike_calc.py.
Probably more. Roughly: hike_calc subparser => CLI command.

"""


import sys
import argparse
import logging
import cmd
import os.path

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

    def parse_shortest(self, arg):
        parser = argparse.ArgumentParser(prog='shortest')
        parser.add_argument('-w', '--waypoint',
                            action='append',
                            help='Waypoint to include. (multi allowed)')
        parser.add_argument('-c', '--camp',
                            nargs=2,
                            action='append',
                            help=('(waypoint night-number) of camp. Reset '
                                  'distance. (multi allowed)'))
        parser.add_argument('--details',
                            action='store_true',
                            help='List cummulative distance)')
        parser.add_argument('--prefix_camp',
                            default='',
                            help=('Prefix camp number with this string when '
                                  'outputting details.'))
        parser.add_argument('--first_day',
                            help='Date (mm/dd/yyyy) of first day of hiking')
        return parser.parse_args(arg.split())

    def parse_load(self, arg):
        parser = argparse.ArgumentParser(prog='load')
        parser.add_argument('datafile', help='Input data file')
        parser.add_argument('-f', '--format',
                            choices=['csv', 'path', 'yaml'],
                            default='path',
                            help='Data format'
                            )
        return parser.parse_args(arg.split())

    def argparse_help(self, parser):
        try:
            print(parser('-h'))
        except SystemExit:
            pass
    
    ###########################################################################
    ### ----- HikeCalc commands --------
    def help_load(self):
        self.argparse_help(self.parse_load)
    def do_load(self, arg):
        """\
Load datafile.
SYNTAX: load [options] filename 
OPTIONS:
 format::
EXAMPLE:
    load ~/sandbox/hikecalc/data/catalina.dat
"""
        args = self.parse_load(arg)
        try:
            self.hiker.loadData(open(os.path.expanduser(args.datafile)),
                                args.format)
            if args.format != 'yaml':
                self.hiker.appendTrailHeadsByPattern()
        except Exception as err:
            print('File not loaded')
            print(err)
        else:
            print('File loaded. Use "th" for list of trail-heads, '
                  '"wp" for waypoints.')
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
    def help_shortest(self):
        self.argparse_help(self.parse_shortest)
    def do_shortest(self, arg):
        """\
Display shortest route that passes through list of waypoints.
SYNTAX: shortest wpname[.camp1...] ...
EXAMPLE:
    load ~/hikecalc/data/catalina.dat
    shortest SabinoTH HutchsPool
"""
        
        #waypoints,camps = self.parse_waypoints(arg)
        #hc.shortest(self.hiker, waypoints, camps=camps, verbose=True)
        args = self.parse_shortest(arg)
        hc.shortest(self.hiker, args.waypoint, camps=args.camp,
                    verbose=args.details)
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

    
