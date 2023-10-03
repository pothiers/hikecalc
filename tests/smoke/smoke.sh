#!/bin/bash
# PURPOSE:    Wrapper for smoke test
# EXAMPLE:
#   ./tests/smoke/smoke.sh

file=$0
dir=`dirname $file`
origdir=`pwd`
cd $dir

source smoke-lib.sh
return_code=0

SMOKEOUT="README-smoke-results.txt"
CLIOUT="session.in"
DISTOUT="catalina-dist.csv"

export CD=~/sandbox/hikecalc/data/catalina.dat


echo ""
echo "Starting tests in \"$dir\" ..."
echo ""
echo ""

testCommand hc_help_1  "hc --help 2>&1"            "^\#" n
testCommand hc_help_2  "hc shortest --help 2>&1"   "^\#" n

# What trailheads are in the file?
testCommand hc_th_0    "hc th $CD"                 "^\#" n

# What waypoints are in the file?
testCommand hc_wp_0    "hc wp $CD"                 "^\#" n

# How far is it from Sabino visitor center to The Window?
testCommand hc_short_0 "hc shortest -w SabinoTH -w TheWindow $CD"    "^\#" n

# What is the detail distance from Butterfly to Palisades Ranger Station?
cmd="hc shortest -w ButterflyTH -w PalisadesRangerTH --details $CD"
testCommand hc_short_1 "$cmd"                             "^\#" n

# Basic multi-day route
cmd="hc shortest --details -w MarshallGulchTH -w SabinoTH $CD"
testCommand hc_multi_0 "$cmd" "^\#" n
# With Camps
cmd="hc shortest --details -w MarshallGulchTH -w SabinoTH -c LemmonPoolJct 1 -c WestForkTE 2 -c BridalVeilFalls 3 $CD"
testCommand hc_multi_1 "$cmd" "^\#" n

#! cat > $CLIOUT <<EOF
#! load NO-FILE.dat
#! load ~/sandbox/hikecalc/data/catalina.dat
#! EOF
#! testCommand cli0_1 "hikecalc < $CLIOUT 2>&1" "^\#" n
#!
#! cat > $CLIOUT <<EOF
#! load ~/sandbox/hikecalc/data/catalina.dat
#! th
#! EOF
#! testCommand cli2_1 "hikecalc < $CLIOUT 2>&1" "^\#" n
#!
#! cat > $CLIOUT <<EOF
#! load ~/sandbox/hikecalc/data/catalina.dat
#! wp
#! EOF
#! testCommand cli3_1 "hikecalc < $CLIOUT 2>&1" "^\#" n
#!
#! #!cat > $CLIOUT <<EOF
#! #!load ~/sandbox/hikecalc/data/catalina.dat
#! #!shortest SabinoTH HutchsPool
#! #!EOF
#! #!testCommand cli1_1 "hikecalc < $CLIOUT 2>&1" "^\#" n
#! cat > $CLIOUT <<EOF
#! load ~/sandbox/hikecalc/data/catalina.dat
#! shortest --details -w SabinoTH -w HutchsPool
#! EOF
#! testCommand cli1_1 "hikecalc < $CLIOUT 2>&1" "^\#" n
#!
#! cat > $CLIOUT <<EOF
#! load ~/sandbox/hikecalc/data/catalina.dat
#! dist dist.out
#! EOF
#! testCommand cli4_1 "hikecalc < $CLIOUT 2>&1" "^\#" n
#! sort dist.out > $DISTOUT
#! testOutput  cli4_2 $DISTOUT '^\#' n


###########################################
#! echo "WARNING: ignoring remainder of tests"
#! exit $return_code
###########################################


##############################################################################

rm $SMOKEOUT 2>/dev/null
if [ $return_code -eq 0 ]; then
  echo ""
  echo "ALL smoke tests PASSED ($SMOKEOUT created)"
  echo "All tests passed on " `date` > $SMOKEOUT
else
  echo "Smoke FAILED (no $SMOKEOUT produced)"
fi

##############################################################################
### Don't move or remove!
cd $origdir
exit $return_code
