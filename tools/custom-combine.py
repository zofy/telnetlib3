#!/usr/bin/env python
"""Simple script provides coverage combining across build chains."""
# pylint: disable=invalid-name
from __future__ import print_function

# local
import subprocess
import tempfile
import shutil
import glob
import os

# 3rd-party
import coverage
import six

PROJ_ROOT = os.path.join(os.path.dirname(__file__), os.pardir)
COVERAGERC = os.path.join(PROJ_ROOT, '.coveragerc')


def main():
    """Program entry point."""
    cov = coverage.Coverage(config_file=COVERAGERC)
    assert os.path.abspath(PROJ_ROOT) == os.path.abspath(os.getcwd()), (
        # it would seem coverage.py has no variables that manage the input and
        # output folder path, it must use getcwd() under the hood -- make sure
        # its the one we want.
        'Coverage must be executed from the root project folder',
        os.getcwd(), PROJ_ROOT)

    # we must duplicate these files, coverage.py unconditionally
    # deletes them on .combine().
    _data_paths = glob.glob(os.path.join(PROJ_ROOT, '._coverage.*'))
    dst_folder = tempfile.mkdtemp()
    data_paths = []
    for src in _data_paths:
        dst = os.path.join(dst_folder, os.path.basename(src))
        shutil.copy(src, dst)
        data_paths.append(dst)

    print("combining coverage: {0}".format(data_paths))
    cov.combine(data_paths=data_paths)
    cov.load()
    cov.html_report(ignore_errors=True)
    print("--> open {0}/htmlcov/index.html for review."
          .format(os.path.relpath(PROJ_ROOT)))

    fout = six.StringIO()
    cov.report(file=fout, ignore_errors=True)
    header = u''
    for line in fout.getvalue().splitlines():
        if not header and line:
            header = line
        if u'TOTAL' in line:
            total_line = line
            break
    else:
        raise ValueError("'TOTAL' summary not found in summary output")

    _, no_stmts, no_miss, _ = total_line.split(None, 3)
    no_covered = int(no_stmts) - int(no_miss)

    print("##teamcity[buildStatisticValue "
          "key='CodeCoverageAbsLTotal' "
          "value='{0}']".format(no_stmts))
    print("##teamcity[buildStatisticValue "
          "key='CodeCoverageAbsLCovered' "
          "value='{0}']".format(no_covered))
    print(header)
    print(total_line)

if __name__ == '__main__':
    main()
