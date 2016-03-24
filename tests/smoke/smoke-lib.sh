#!/bin/bash
# PURPOSE:    Routines to make writing smoke tests easier
#
# NOTES:
#   Generally the functions here try to make it easy to compare
#   current program output with past program output.  Its up to you to
#   make sure that some particular output is "right".  In this
#   context,  "output" can be one or more of the following:
#      - Output from a command: (stdout)
#      - Error from a command: (stderr, should be empty)
#      - Data files written by a command.
#      - Modifications that a command makes to a DB. (compare results of
#        query run after command)
#
#
# AUTHORS:    S. Pothier
##############################################################################

##
## Test a module that modifies a database.
## 
function dBtestBlock () {
  proc=dBtestBlock
  actual_prog_out=$1
  actual_db_out=$2
  testName=$3
  progName=$4
  
  # Initialize the DB to a known state. (at least for portions we care about)
  reset-db.sh
  # How do I make this general??
  bec -go ../data/rec_sub_collection.xml > /dev/null
  
  GOLD=${actual_prog_out}.GOLD
  
  java  -DSANDBOX=$SANDBOX $progName > ${actual_prog_out}
  #! java  $progName | tee ${actual_prog_out}
  
  # filter out diagnostic output
  egrep -v '^;' ${actual_prog_out} > ${actual_prog_out}.clean
  egrep -v '^;' $GOLD > $GOLD.clean
  
  if ! diff $GOLD.clean ${actual_prog_out}.clean > diff.out
  then
    cat diff.out
    pwd=`pwd`
    echo "To accept current results: cp $pwd/${actual_prog_out} $pwd/$GOLD"
    echo "*** $proc FAILED [$testName] (1/2; test output missmatch) ***"
    return_code=1
  else
    echo "*** $proc PASSED [$testName] (1/2) ***"
  fi
  
  GOLD=${actual_db_out}.GOLD
  
  # Get report on DB to make sure we modified the DB content correctly.
  report-db.sh > ${actual_db_out}
  
  
  # filter out non-constant values
  egrep -v '^createtime' ${actual_db_out} \
     | egrep -v '^SELECT ' $GOLD \
     | egrep -v '^-\[ RECORD ' > ${actual_db_out}.clean
  egrep -v '^createtime' $GOLD \
     | egrep -v '^SELECT ' $GOLD \
     | egrep -v '^-\[ RECORD ' > $GOLD.clean
  
  if ! diff $GOLD.clean ${actual_db_out}.clean > diff-db.out
  then
    cat diff-db.out
    pwd=`pwd`
    echo "To accept current results: cp $pwd/${actual_db_out} $pwd/$GOLD"
    echo "*** $proc FAILED [$testName] (2/2; DB content mismatch) ***"
    return_code=1
  else
    echo "*** $proc PASSED [$testName] (2/2) ***"
  fi
} # end dBtestBlock


##
## Run a Guile script and compare its ACTUAL stdout to EXPECTED stdout.
## Ignore lines that start with COMMENT (defaults to ";")
##
function testScm () {
  proc=testScm
  scm=$1           # Scheme file without .scm suffix
  COMMENT=${2:-";"}
 
  actual="$scm.out"
  err="$scm.err"
  GOLD="${actual}.GOLD"
  testName="$scm.test"
  diff="diff.scm.out"
  

  cmd="guile < $scm.scm > $actual 2> $err"
  echo "EXECUTING: $cmd"
  eval $cmd 

  ## Make sure we didn't get errors (output to stderr).
  tn="2/3"
  ERRGOLD=$err.GOLD
  pwd=`pwd`
  if [ -e $ERRGOLD ]; then
      sort $ERRGOLD  > $ERRGOLD.sorted
      sort $err  > $err.sorted
      if ! diff $ERRGOLD.sorted $err.sorted > $diff;  then
          cat $diff
          echo ""
          echo "To accept current results: cp $pwd/$err $pwd/$ERRGOLD"
          echo "*** $proc FAILED [$testName] ($tn; got UNEXPECTED STDERR) ***"
          return_code=1
      else
          echo "*** $proc PASSED [$testName] ($tn; got expected STDERR) ***"
          rm $ERRGOLD.sorted $err.sorted
      fi
  else
      if [ -s $err ]; then
        cat $err
        echo "*** $proc FAILED [$testName] ($tn; Output was sent to STDERR: $err) ***"
        echo ""
        echo "To accept current STDERR results: cp $pwd/$err $pwd/$ERRGOLD"
        echo "*** $proc FAILED [$testName] ($tn; got UNEXPECTED STDERR) ***"
        return_code=1
      else
        echo "*** $proc PASSED [$testName] ($tn; no STDERR output) ***"
        rm $err
      fi
  fi

  # filter out diagnostic output (if any)
  egrep -v "^${COMMENT}" $actual > $actual.clean
  egrep -v "^${COMMENT}" $GOLD > $GOLD.clean

  if ! diff $GOLD.clean $actual.clean > $diff;  then
      cat $diff
      pwd=`pwd`
      echo ""
      echo "To accept current results: cp $pwd/$actual $pwd/$GOLD"
      echo "*** $proc FAILED [$testName] (2/2; got UNEXPECTED STDOUT) ***"
      return_code=1
  else
      echo "*** $proc PASSED [$testName] (2/2; got expected STDOUT) ***"
      rm $diff $GOLD.clean $actual.clean
  fi
}  # END testScm

##
## Run given CMD and compare its ACTUAL stdout to EXPECTED stdout.
## Ignore lines that start with COMMENT (defaults to ";")
##
function testCommand () {
  proc=testCommand
  testName="$1" # No Spaces; e.g. CCUE
  CMD="$2"
  COMMENT=${3:-"^;"}
  displayOutputP=${4:-"y"}      # or "n" to save stdout to file only
  expectedStatus=${5:-0}

  actual="${testName}.out"
  err="${testName}.err"
  GOLD="${actual}.GOLD"
  diff="diff.out"
  

  # This isn't a great solution since it only works with bash, but it gets
  # me by.
  # 
  # The PIPESTATUS is a special bash variable which is an array.  Since I
  # didn't give a subscript, I got the first element which is what I
  # wanted.

  #! echo "EXECUTING: $cmd"
  tn="1/3"
  #! cmd="${CMD} 2> $err | tee $actual"
  #! echo "CMD=$CMD"
  if [ "y" = "$displayOutputP" ]; then
    eval ${CMD} 2> $err | tee $actual
  else
    eval ${CMD} 2> $err > $actual
  fi
  actualStatus=$PIPESTATUS
  if [ $actualStatus -ne $expectedStatus ]; then
    echo "Failed command: ${CMD}"
    echo "*** $proc FAILED [$testName] ($tn; Command returned unexpected status; got $actualStatus <> $expectedStatus) ***"
    return_code=1
  else
    echo "*** $proc PASSED [$testName] ($tn; Command correctly returned zero status ***"
  fi
  


  ## Make sure we didn't get errors (output to stderr).
  tn="2/3"
  if [ -s $err ]; then
    cat $err
    echo "*** $proc FAILED [$testName] ($tn; Output was sent to STDERR: $err) ***"
    return_code=1
  else
    echo "*** $proc PASSED [$testName] ($tn; no STDERR output) ***"
    rm $err
  fi

  # filter out diagnostic output (if any)
  #! echo "DEBUG: COMMENT=${COMMENT}"
  egrep -v ${COMMENT} $actual > $actual.clean
  egrep -v ${COMMENT} $GOLD > $GOLD.clean

  tn="3/3"
  if ! diff $GOLD.clean $actual.clean > $diff;  then
      cat $diff
      pwd=`pwd`
      echo ""
      echo "To accept current results: cp $pwd/$actual $pwd/$GOLD"
      echo "*** $proc FAILED [$testName] ($tn; got UNEXPECTED STDOUT) ***"
      return_code=1
  else
      echo "*** $proc PASSED [$testName] ($tn; got expected STDOUT) ***"
      rm $diff $GOLD.clean $actual.clean
  fi
}  # END testCommand

##
## Make sure a generated output file matches expected.
## Ignore lines that match regular expression VARIANT (defaults to "^;")
##
function testOutput () { 
  proc=testOutput
  testName="$1" # No Spaces; e.g. CCUE
  output=$2
  GOLD=${output}.GOLD

  VARIANT=${3:-"^;"}
  displayOutputP=${4:-"y"}      # or "n" to save stdout to file only
  diff="${output}.diff"

  # filter out diagnostic output (if any)
  egrep -v "${VARIANT}" $output > $output.clean
  egrep -v "${VARIANT}" $GOLD > $GOLD.clean

  if ! diff $GOLD.clean $output.clean > $diff;  then
      if [ "y" = "$displayOutputP" ]; then
          cat $diff
      else
          echo ""
          echo "[$testName] DIFF between ACTUAL and EXPECTED output is in: "
          echo "  `pwd`/$diff"
          echo ""
      fi
      pwd=`pwd`
      echo ""
      echo "To accept current results: cp $pwd/$output $pwd/$GOLD"
      echo "*** $proc  FAILED  [$testName] (got UNEXPECTED output in: $output) ***"
      return_code=1
  else
      echo "*** $proc  PASSED [$testName] (got expected output in: $output) ***"
      rm $diff $GOLD.clean $output.clean
  fi
}

##############################################################################
