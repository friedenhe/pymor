#!/bin/bash

THIS_DIR="$(cd "$(dirname ${BASH_SOURCE[0]})" ; pwd -P )"
source ${THIS_DIR}/common_test_setup.bash

sudo apt update && sudo apt install -y mmv
# as a workaround intermittent MPI finalize errors which we
# cannot seem to directly affect, we save the intermediate
# pytest exit code in a file and check that afterwards
# while ignoring the mpirun result itself
RANKS=2
xvfb-run -a mpirun --output-filename mpi_logs --report-state-on-timeout \
  --get-stack-traces --timestamp-output --tag-output --timeout 1200 \
  --mca btl self,vader -n ${RANKS} python -u -m coverage run --rcfile=setup.cfg \
  --parallel-mode src/pymortests/mpi_run_demo_tests.py || true

mmv mpi_logs/\*/rank.\*/\* mpi_log.rank_#2.#3.txt
rm -rf mpi_logs/

for fn in ./.mpirun_*/pytest.mpirun.success ; do
  [[ "$(cat ${fn})" == "True" ]] || exit 127
done

coverage combine
# the test_thermalblock_ipython results in '(builtin)' missing which we "--ignore-errors"
coverage xml --ignore-errors
