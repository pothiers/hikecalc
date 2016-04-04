#!/bin/bash
# PURPOSE:    Wrapper for smoke test

file=$0
dir=`dirname $file`
origdir=`pwd`
cd $dir

source smoke-lib.sh
return_code=0

SMOKEOUT="README-smoke-results.txt"
CLIOUT="session.in"
DISTOUT="catalina-dist.csv"


echo ""
echo "Starting tests in \"$dir\" ..."
echo ""
echo ""

cat > $CLIOUT <<EOF
load NO-FILE.dat
load ~/sandbox/hikecalc/data/catalina.dat
EOF
testCommand cli0_1 "hikecalc < $CLIOUT 2>&1" "^\#" n

cat > $CLIOUT <<EOF
load ~/sandbox/hikecalc/data/catalina.dat
th
EOF
testCommand cli2_1 "hikecalc < $CLIOUT 2>&1" "^\#" n

cat > $CLIOUT <<EOF
load ~/sandbox/hikecalc/data/catalina.dat
wp
EOF
testCommand cli3_1 "hikecalc < $CLIOUT 2>&1" "^\#" n

#!cat > $CLIOUT <<EOF
#!load ~/sandbox/hikecalc/data/catalina.dat
#!shortest SabinoTH HutchsPool
#!EOF
#!testCommand cli1_1 "hikecalc < $CLIOUT 2>&1" "^\#" n
cat > $CLIOUT <<EOF
load ~/sandbox/hikecalc/data/catalina.dat
shortest --details -w SabinoTH -w HutchsPool
EOF
testCommand cli1_1 "hikecalc < $CLIOUT 2>&1" "^\#" n

cat > $CLIOUT <<EOF
load ~/sandbox/hikecalc/data/catalina.dat
dist dist.out
EOF
testCommand cli4_1 "hikecalc < $CLIOUT 2>&1" "^\#" n
sort dist.out > $DISTOUT
testOutput  cli4_2 $DISTOUT '^\#' n


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

