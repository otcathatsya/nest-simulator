# -*- coding: utf-8 -*-
#
# test_tripartite_connect.py
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

"""
Basic tests for tripartite connectivity.

For statistical tests, see `test_connect_tripartite_bernoulli.py`.
"""

import nest
import pytest


@pytest.fixture(autouse=True)
def reset_kernel():
    """
    Reset kernel to clear connections before each test.
    """

    nest.ResetKernel()


def test_connect_all():
    n_pre, n_post, n_third = 4, 2, 3
    pre = nest.Create("parrot_neuron", n_pre)
    post = nest.Create("parrot_neuron", n_post)
    third = nest.Create("parrot_neuron", n_third)

    nest.TripartiteConnect(
        pre,
        post,
        third,
        {"rule": "pairwise_bernoulli", "p": 1.0},
        {"rule": "third_factor_bernoulli_with_pool", "p": 1.0},
    )

    n_primary = n_pre * n_post
    assert len(nest.GetConnections(pre, post)) == n_primary
    assert len(nest.GetConnections(pre, third)) == n_primary
    assert len(nest.GetConnections(third, post)) == n_primary


def test_connect_astro():
    n_pre, n_post, n_third = 4, 2, 3
    pre = nest.Create("aeif_cond_alpha_astro", n_pre)
    post = nest.Create("aeif_cond_alpha_astro", n_post)
    third = nest.Create("astrocyte_lr_1994", n_third)

    nest.TripartiteConnect(
        pre,
        post,
        third,
        {"rule": "pairwise_bernoulli", "p": 1.0},
        {"rule": "third_factor_bernoulli_with_pool", "p": 1.0},
        {"third_out": {"synapse_model": "sic_connection"}},
    )

    n_primary = n_pre * n_post
    assert len(nest.GetConnections(pre, post)) == n_primary
    assert len(nest.GetConnections(pre, third)) == n_primary
    assert len(nest.GetConnections(third, post)) == n_primary


def test_explicit_random_pool():
    n_pre, n_post, n_third = 4, 2, 3
    pre = nest.Create("parrot_neuron", n_pre)
    post = nest.Create("parrot_neuron", n_post)
    third = nest.Create("parrot_neuron", n_third)

    nest.TripartiteConnect(
        pre,
        post,
        third,
        {"rule": "pairwise_bernoulli", "p": 1.0},
        {"rule": "third_factor_bernoulli_with_pool", "p": 1.0, "pool_type": "random", "pool_size": 2},
    )

    n_primary = n_pre * n_post
    assert len(nest.GetConnections(pre, post)) == n_primary
    assert len(nest.GetConnections(pre, third)) == n_primary
    assert len(nest.GetConnections(third, post)) == n_primary


def test_block_pool_single():
    n_pre, n_post, n_third = 4, 4, 2
    pre = nest.Create("parrot_neuron", n_pre)
    post = nest.Create("parrot_neuron", n_post)
    third = nest.Create("parrot_neuron", n_third)

    nest.TripartiteConnect(
        pre,
        post,
        third,
        {"rule": "pairwise_bernoulli", "p": 1.0},
        {"rule": "third_factor_bernoulli_with_pool", "p": 1.0, "pool_type": "block", "pool_size": 1},
    )

    n_primary = n_pre * n_post
    assert len(nest.GetConnections(pre, post)) == n_primary
    assert len(nest.GetConnections(pre, third)) == n_primary
    assert len(nest.GetConnections(third, post)) == n_primary


def test_block_pool_wide():
    n_pre, n_post, n_third = 4, 2, 8
    pre = nest.Create("parrot_neuron", n_pre)
    post = nest.Create("parrot_neuron", n_post)
    third = nest.Create("parrot_neuron", n_third)

    nest.TripartiteConnect(
        pre,
        post,
        third,
        {"rule": "pairwise_bernoulli", "p": 1.0},
        {"rule": "third_factor_bernoulli_with_pool", "p": 1.0, "pool_type": "block", "pool_size": 4},
    )

    n_primary = n_pre * n_post
    assert len(nest.GetConnections(pre, post)) == n_primary
    assert len(nest.GetConnections(pre, third)) == n_primary
    assert len(nest.GetConnections(third, post)) == n_primary


def test_tripartite_raises():
    n_pre, n_post, n_third = 4, 2, 8
    pre = nest.Create("parrot_neuron", n_pre)
    post = nest.Create("parrot_neuron", n_post)
    third = nest.Create("parrot_neuron", n_third)

    with pytest.raises(nest.kernel.NESTErrors.IllegalConnection):
        nest.TripartiteConnect(pre, post, third, {"rule": "one_to_one"}, {"rule": "one_to_one"})


def test_tripartite_rejects_make_symmetric():
    n_pre, n_post, n_third = 4, 4, 8
    pre = nest.Create("parrot_neuron", n_pre)
    post = nest.Create("parrot_neuron", n_post)
    third = nest.Create("parrot_neuron", n_third)

    with pytest.raises(nest.kernel.NESTErrors.BadProperty):
        nest.TripartiteConnect(
            pre,
            post,
            third,
            {"rule": "one_to_one", "make_symmetric": True},
            {"rule": "third_factor_bernoulli_with_pool"},
        )


@pytest.mark.skipif_missing_threads
@pytest.mark.parametrize(
    "connspec, num_conns_expected",
    [
        ({"rule": "one_to_one"}, 6),
        ({"rule": "all_to_all"}, 36),
        ({"rule": "fixed_indegree", "indegree": 3}, 18),
        ({"rule": "fixed_outdegree", "outdegree": 3}, 18),
        ({"rule": "fixed_total_number", "N": 23}, 23),
        ({"rule": "pairwise_bernoulli", "p": 1}, 36),
    ],
)
def test_third_works_for_all_primary_rules(connspec, num_conns_expected):
    nest.local_num_threads = 4
    n = 6  # if this is changed, number of expected connection must be adjusted above
    pre = nest.Create("parrot_neuron", n)
    post = nest.Create("parrot_neuron", n)
    third = nest.Create("parrot_neuron", 5)

    nest.TripartiteConnect(pre, post, third, connspec, {"rule": "third_factor_bernoulli_with_pool", "p": 1.0})

    assert len(nest.GetConnections(pre, post)) == num_conns_expected
    assert len(nest.GetConnections(pre, third)) == num_conns_expected
    assert len(nest.GetConnections(third, post)) == num_conns_expected


@pytest.mark.skipif_missing_threads
def test_sliced_third():
    """Test that connection works on multiple threads when using complex node collection as third factor."""

    nest.local_num_threads = 4
    nrn = nest.Create("parrot_neuron", 20)
    third = (nrn[:3] + nrn[5:])[::3]

    nest.TripartiteConnect(
        nrn,
        nrn,
        third,
        {"rule": "all_to_all"},
        {"rule": "third_factor_bernoulli_with_pool", "pool_type": "random", "pool_size": 2},
    )

    t_in = nest.GetConnections(target=third)
    t_out = nest.GetConnections(source=third)

    assert len(t_in) == len(t_out)
    assert set(t_in.targets()) <= set(third.global_id)
    assert set(t_out.sources()) <= set(third.global_id)


def test_connect_complex_synspecs():
    n_pre, n_post, n_third = 4, 2, 3
    pre = nest.Create("parrot_neuron", n_pre)
    post = nest.Create("parrot_neuron", n_post)
    third = nest.Create("parrot_neuron", n_third)

    nest.TripartiteConnect(
        pre,
        post,
        third,
        {"rule": "pairwise_bernoulli", "p": 1.0},
        {"rule": "third_factor_bernoulli_with_pool", "p": 1.0},
        {
            "primary": nest.CollocatedSynapses(
                {"synapse_model": "stdp_synapse", "weight": 2.0}, {"synapse_model": "tsodyks_synapse", "delay": 3.0}
            ),
            "third_in": nest.CollocatedSynapses(
                {"synapse_model": "static_synapse", "weight": nest.random.uniform(0.5, 1.5)},
                {"synapse_model": "tsodyks2_synapse"},
            ),
            "third_out": nest.CollocatedSynapses(
                {"synapse_model": "static_synapse_lbl"},
                {"synapse_model": "stdp_synapse_hpc", "alpha": nest.random.uniform(0.5, 1.5)},
            ),
        },
    )

    n_primary = n_pre * n_post
    c_stdp = nest.GetConnections(synapse_model="stdp_synapse")
    assert len(c_stdp) == n_primary
    assert set(c_stdp.weight) == {2.0}

    c_tsodyks = nest.GetConnections(synapse_model="tsodyks_synapse")
    assert len(c_tsodyks) == n_primary
    assert set(c_tsodyks.delay) == {3.0}

    c_static = nest.GetConnections(synapse_model="static_synapse")
    assert len(c_static) == n_primary
    assert len(set(c_static.weight)) == len(c_static)  # random values, all different

    c_tsodyks2 = nest.GetConnections(synapse_model="tsodyks2_synapse")
    assert len(c_tsodyks2) == n_primary
    assert set(c_tsodyks2.delay) == {1.0}

    c_stat_lbl = nest.GetConnections(synapse_model="static_synapse_lbl")
    assert len(c_stat_lbl) == n_primary
    assert set(c_stat_lbl.weight) == {1.0}

    c_stdp_hpc = nest.GetConnections(synapse_model="stdp_synapse_hpc")
    assert len(c_stdp_hpc) == n_primary
    assert len(set(c_stdp_hpc.alpha)) == len(c_stdp_hpc)  # random values, all different
