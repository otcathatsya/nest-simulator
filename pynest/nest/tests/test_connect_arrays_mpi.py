# -*- coding: utf-8 -*-
#
# test_connect_arrays_mpi.py
#
# This file is part of NEST.
#
# Copyright (C) 2004 The NEST Initiative
#
# NEST is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# NEST is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NEST.  If not, see <http://www.gnu.org/licenses/>.

import os
import subprocess as sp
import unittest
import nest
import numpy as np

try:
    from mpi4py import MPI
    HAVE_MPI4PY = True
except ImportError:
    HAVE_MPI4PY = False

HAVE_MPI = nest.ll_api.sli_func("statusdict/have_mpi ::")
MULTIPLE_PROCESSES = nest.NumProcesses() > 1


class ConnectArraysMPICase(unittest.TestCase):
    non_unique = np.array([1, 1, 3, 5, 4, 5, 9, 7, 2, 8], dtype=np.uint64)
    comm = MPI.COMM_WORLD

    # With nosetests, only run these tests if using multiple processes
    __test__ = MULTIPLE_PROCESSES

    def assert_connections(self, expected_sources, expected_targets, rule='one_to_one'):
        """Gather connections from all processes and assert against expected connections"""
        conns = nest.GetConnections()
        projections = [[s, t] for s, t in zip(conns.source, conns.target)]
        if rule == 'one_to_one':
            expected_projections = np.array([[s, t] for s, t in zip(expected_sources, expected_targets)])
        elif rule == 'all_to_all':
            expected_projections = np.array([[s, t] for s in expected_sources for t in expected_targets])
        else:
            self.assertFalse(True, 'rule={} is not valid'.format(rule))

        recv_projections = self.comm.gather(projections, root=0)
        if self.comm.Get_rank() == 0:
            # Flatten the projection lists to a single list of projections
            recv_projections = np.array([proj for part in recv_projections for proj in part])
            # Results must be sorted to make comparison possible
            np.testing.assert_array_equal(np.sort(recv_projections, axis=0), np.sort(expected_projections, axis=0))
        else:
            self.assertIsNone(recv_projections)

    def setUp(self):
        nest.ResetKernel()

    def test_connect_arrays_unique(self):
        """Connecting NumPy arrays of unique node IDs with MPI"""
        n = 10
        nest.Create('iaf_psc_alpha', n)
        sources = np.arange(1, n+1, dtype=np.uint64)
        targets = np.arange(1, n+1, dtype=np.uint64)
        weights = 1.5
        delays = 1.4

        nest.Connect(sources, targets, syn_spec={'weight': weights, 'delay': delays})

        self.assert_connections(sources, targets, rule='all_to_all')

    def test_connect_arrays_nonunique(self):
        """Connecting NumPy arrays with non-unique node IDs with MPI"""
        n = 10
        nest.Create('iaf_psc_alpha', n)
        sources = np.arange(1, n+1, dtype=np.uint64)
        targets = self.non_unique
        weights = np.ones(n)
        delays = np.ones(n)
        nest.Connect(sources, targets, syn_spec={'weight': weights, 'delay': delays},
                     conn_spec='one_to_one')

        self.assert_connections(sources, targets)

    def test_connect_arrays_threaded(self):
        """Connecting NumPy arrays, threaded with MPI"""
        nest.SetKernelStatus({'local_num_threads': 2})
        n = 10
        nest.Create('iaf_psc_alpha', n)
        sources = np.arange(1, n+1, dtype=np.uint64)
        targets = self.non_unique
        weights = np.ones(len(sources))
        delays = np.ones(len(sources))
        syn_model = 'static_synapse'

        nest.Connect(sources, targets, conn_spec='one_to_one',
                     syn_spec={'weight': weights, 'delay': delays, 'synapse_model': syn_model})

        self.assert_connections(sources, targets)


class TestConnectArraysMPI(unittest.TestCase):

    # With nosetests, only run this test if using a single process
    __test__ = not MULTIPLE_PROCESSES

    @unittest.skipIf(not HAVE_MPI, 'NEST was compiled without MPI')
    @unittest.skipIf(not HAVE_MPI4PY, 'mpi4py is not available')
    def testWithMPI(self):
        """Connect NumPy arrays with MPI"""
        directory = os.path.dirname(os.path.realpath(__file__))
        script = os.path.realpath(__file__)
        test_script = os.path.join(directory, script)
        command = nest.ll_api.sli_func("mpirun", 2, "nosetests", test_script)
        command = command.split()

        my_env = os.environ.copy()
        retcode = sp.call(command, env=my_env)

        self.assertEqual(retcode, 0, 'Test failed when run with "mpirun -np 2 nosetests [script]"')


if __name__ == '__main__':
    raise RuntimeError('This test must be run with nosetests or pytest')
