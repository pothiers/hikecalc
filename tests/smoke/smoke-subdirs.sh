#!/bin/sh
# Time-stamp: <09-20-2010 10:03:15 smoke-subdirs.sh>
#
# PURPOSE: Run smoke tests on all subdirs that have smoke.sh

here=`pwd`
for d in `find . -name smoke.sh -printf "%h "`; do
    echo "Running smoke on: $d"
    cd $d
    smoke.sh
    cd $here
done

echo ""
echo "Smoke summary"
find . -name smoke.out -printf "%10h/%f: " -exec cat {} \;
