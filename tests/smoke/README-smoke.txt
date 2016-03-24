This directory contains "smoke tests".

Smoke tests are intended to be easy to create tests that run
quickly. Run time more than a few minutes is NOT considered quick.
They are expected to be used just before checkin and after
checkout to answer the question: "Does it seem to working ok?".

They are definitely NOT either "regression" or "unit" tests.
They are not regression tests because they don't try to cover a lot of
cases (which would cause them to take too long to run). They are not
unit tests because they are done at the level of PROGRAM output, not
internal functions.

Because smoke tests are easy to create and run, they are appropriate
for prototype code.  They help developers be more courageous by
requiring less inspection to determine if specific changes broke
anything.

For software further along in Technical Readiness Level, regression
and unit tests should also be used.

