# -*- coding: utf-8 -*-
#
# __init__.py
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

r"""PyNEST - Python interface for the NEST simulator

* ``nest.helpdesk()`` opens the NEST documentation in your browser.

* ``nest.__version__`` displays the NEST version.

* ``nest.Models()`` shows all available neuron, device and synapse models.

* ``nest.help('model_name') displays help for the given model, e.g., ``nest.help('iaf_psc_exp')``

* To get help on functions in the ``nest`` package, use Python's ``help()`` function
  or IPython's ``?``, e.g.

     - ``help(nest.Create)``
     - ``nest.Connect?``

For more information visit https://www.nest-simulator.org.
"""

# WARNING: This file is only used to create the `NestModule` below and then
# ignored. If you'd like to make changes to the root `nest` module, they need to
# be made to the `NestModule` class/instance instead.

################

# Store interpreter-given module attributes to copy into replacement module
# instance later on. Use `.copy()` to prevent pollution with other variables
_original_module_attrs = globals().copy()

from .ll_api import KernelAttribute  # noqa
import sys                           # noqa
import types                         # noqa
import importlib                     # noqa

try:
    import versionchecker
except ImportError:
    pass


def _rel_import_star(module, import_module_name):
    """Emulates `from X import *` into `module`"""

    imported = importlib.import_module(import_module_name, __name__)
    imp_iter = vars(imported).items()
    if hasattr(module, "__all__"):
        # If a public api is defined using the `__all__` attribute, copy that.
        module.update(kv for kv in imp_iter if kv[0] in imported.__all__)
    else:
        # Otherwise follow "underscore is private" convention.
        module.update(kv for kv in imp_iter if not kv[0].startswith("_"))


def _lazy_module_property(module_name, optional=False, optional_hint=""):
    """
    Returns a property that lazy loads a module and substitutes itself with it.
    The class variable name must match given `module_name`::

      class ModuleClass(types.ModuleType):
          lazy_module_xy = _lazy_module_property("lazy_module_xy")

    :param module_name: Name of the lazy loadable module.
    :type module_name: str
    :param optional: Optional modules raise more descriptive errors.
    :type optional: bool
    :param optional_hint: Message appended in case of import errors, to help
      users install missing optional modules
    :type optional_hint: str
    """
    def lazy_loader(self):
        cls = type(self)
        delattr(cls, module_name)
        try:
            module = importlib.import_module("." + module_name, __name__)
        except ImportError as e:
            if optional:
                raise ImportError(
                    f"This functionality requires the optional module "
                    + module_name + ". " + optional_hint
                ) from None
            else:
                raise e from None
        setattr(cls, module_name, module)
        return module

    return property(lazy_loader)


class NestModule(types.ModuleType):
    """
    A module class for the `nest` root module to control the dynamic generation
    of module level attributes such as the KernelAttributes, lazy loading
    some submodules and importing the public APIs of the `lib` submodules.
    """

    from . import ll_api                             # noqa
    from . import pynestkernel as kernel             # noqa
    from . import random                             # noqa
    from . import math                               # noqa
    from . import spatial_distributions              # noqa
    from . import logic                              # noqa

    __version__ = ll_api.sli_func("statusdict /version get")

    # Lazy load the `spatial` module to avoid circular imports.
    spatial = _lazy_module_property("spatial")

    # Define the kernel attributes.
    #
    # FORMATTING NOTES:
    # * Multiline strings render incorrectly, join multiple single-quote
    #   strings instead.
    # * Strings containing `:` render incorrectly.
    # * Do not end docstrings with punctuation. A `.` or `,` is added by the
    #   formatting logic.

    kernel_status = KernelAttribute(
        "dict", "Get the complete kernel status", readonly=True
    )
    resolution = KernelAttribute(
        "float", "The resolution of the simulation (in ms)", default=0.1
    )
    biological_time = KernelAttribute(
        "float", "The current simulation time (in ms)"
    )
    to_do = KernelAttribute(
        "int", "The number of steps yet to be simulated", readonly=True
    )
    max_delay = KernelAttribute(
        "float", "The maximum delay in the network", default=0.1
    )
    min_delay = KernelAttribute(
        "float", "The minimum delay in the network", default=0.1
    )
    ms_per_tic = KernelAttribute(
        "float", "The number of milliseconds per tic", default=0.001
    )
    tics_per_ms = KernelAttribute(
        "float", "The number of tics per millisecond", default=1000.0
    )
    tics_per_step = KernelAttribute(
        "int", "The number of tics per simulation time step", default=100
    )
    T_max = KernelAttribute(
        "float", "The largest representable time value", readonly=True
    )
    T_min = KernelAttribute(
        "float", "The smallest representable time value", readonly=True
    )
    rng_types = KernelAttribute(
        "list[str]",
        "List of available random number generator types",
        readonly=True,
    )
    rng_type = KernelAttribute(
        "str",
        "Name of random number generator type used by NEST",
        default="mt19937_64",
    )
    rng_seed = KernelAttribute(
        "int",
        (
            "Seed value used as base for seeding NEST random number generators "
            + r"(:math:`1 \leq s\leq 2^{32}-1`)"
        ),
        default=143202461,
    )
    total_num_virtual_procs = KernelAttribute(
        "int", "The total number of virtual processes", default=1
    )
    local_num_threads = KernelAttribute(
        "int", "The local number of threads", default=1
    )
    num_processes = KernelAttribute(
        "int", "The number of MPI processes", readonly=True
    )
    off_grid_spiking = KernelAttribute(
        "bool",
        "Whether to transmit precise spike times in MPI communication",
        readonly=True,
    )
    adaptive_spike_buffers = KernelAttribute(
        "bool",
        "Whether MPI buffers for communication of spikes resize on the fly",
        default=True,
    )
    adaptive_target_buffers = KernelAttribute(
        "bool",
        "Whether MPI buffers for communication of connections resize on the fly",
        default=True,
    )
    buffer_size_secondary_events = KernelAttribute(
        "int",
        (
            "Size of MPI buffers for communicating secondary events "
            + "(in bytes, per MPI rank, for developers)"
        ),
        readonly=True,
    )
    buffer_size_spike_data = KernelAttribute(
        "int",
        "Total size of MPI buffer for communication of spikes",
        default=2,
    )
    buffer_size_target_data = KernelAttribute(
        "int",
        "Total size of MPI buffer for communication of connections",
        default=2,
    )
    growth_factor_buffer_spike_data = KernelAttribute(
        "float",
        (
            "If MPI buffers for communication of spikes resize on the fly, "
            + "grow them by this factor each round"
        ),
        default=1.5,
    )
    growth_factor_buffer_target_data = KernelAttribute(
        "float",
        (
            "If MPI buffers for communication of connections resize on the "
            + "fly, grow them by this factor each round"
        ),
        default=1.5,
    )
    max_buffer_size_spike_data = KernelAttribute(
        "int",
        "Maximal size of MPI buffers for communication of spikes",
        default=8388608,
    )
    max_buffer_size_target_data = KernelAttribute(
        "int",
        "Maximal size of MPI buffers for communication of connections",
        default=16777216,
    )
    use_wfr = KernelAttribute(
        "bool", "Whether to use waveform relaxation method", default=True
    )
    wfr_comm_interval = KernelAttribute(
        "float",
        "Desired waveform relaxation communication interval",
        default=1.0,
    )
    wfr_tol = KernelAttribute(
        "float",
        "Convergence tolerance of waveform relaxation method",
        default=0.0001,
    )
    wfr_max_iterations = KernelAttribute(
        "int",
        "Maximal number of iterations used for waveform relaxation",
        default=15,
    )
    wfr_interpolation_order = KernelAttribute(
        "int",
        "Interpolation order of polynomial used in wfr iterations",
        default=3
    )
    max_num_syn_models = KernelAttribute(
        "int", "Maximal number of synapse models supported", readonly=True
    )
    sort_connections_by_source = KernelAttribute(
        "bool",
        (
            "Whether to sort connections by their source; increases"
            + " construction time of presynaptic data structures, decreases"
            + " simulation time if the average number of outgoing connections"
            + " per neuron is smaller than the total number of threads"
        ),
        default=True,
    )
    structural_plasticity_synapses = KernelAttribute(
        "dict",
        (
            "Defines all synapses which are plastic for the structural"
            + " plasticity algorithm. Each entry in the dictionary is composed"
            + " of a synapse model, the presynaptic element and the"
            + " postsynaptic element"
        ),
    )
    structural_plasticity_update_interval = KernelAttribute(
        "int",
        (
            "Defines the time interval in ms at which the structural plasticity"
            + " manager will make changes in the structure of the network ("
            + " creation and deletion of plastic synapses)"
        ),
        default=10000.0,
    )
    use_compressed_spikes = KernelAttribute(
        "bool",
        (
            "Whether to use spike compression; if a neuron has targets on"
            + " multiple threads of a process, this switch makes sure that only"
            + " a single packet is sent to the process instead of one packet"
            + " per target thread; requires"
            + " ``nest.sort_connections_by_source = True``"
        ),
        default=True,
    )
    data_path = KernelAttribute(
        "str",
        "A path, where all data is written to, defaults to current directory",
    )
    data_prefix = KernelAttribute("str", "A common prefix for all data files")
    overwrite_files = KernelAttribute(
        "bool", "Whether to overwrite existing data files", default=False
    )
    print_time = KernelAttribute(
        "bool",
        "Whether to print progress information during the simulation",
        default=False,
    )
    network_size = KernelAttribute(
        "int", "The number of nodes in the network", readonly=True
    )
    num_connections = KernelAttribute(
        "int",
        "The number of connections in the network",
        readonly=True,
        localonly=True,
    )
    local_spike_counter = KernelAttribute(
        "int",
        (
            "Number of spikes fired by neurons on a given MPI rank during the"
            + " most recent call to :py:func:`.Simulate`. Only spikes from"
            + " \"normal\" neurons are counted, not spikes generated by devices"
            + " such as ``poisson_generator``"
        ),
        readonly=True,
    )
    recording_backends = KernelAttribute(
        "dict[str, dict]",
        (
            "Dict of backends for recording devices. Each recording backend can"
            + " have a set of global parameters that can be modified through"
            + " this attribute by passing a dictionary with the name of the"
            + " recording backend as key and a dictionary with the global"
            + " parameters to be overwritten as value.\n\n"
            + "Example\n"
            + "~~~~~~~\n\n"
            + "Please note that NEST must be compiled with SionLIB for the"
            + " ``sionlib`` backend to be available.\n\n"
            + ".. code-block:: python\n\n"
            + "  nest.recording_backends = dict(sionlib=dict(buffer_size=1024))"
            + "\n\n"
            + ".. seealso:: The valid global parameters are listed in the"
            + " documentation of each recording backend"
        ),
    )
    dict_miss_is_error = KernelAttribute(
        "bool",
        "Whether missed dictionary entries are treated as errors",
        default=True,
    )
    keep_source_table = KernelAttribute(
        "bool",
        "Whether to keep source table after connection setup is complete",
        default=True,
    )
    min_update_time = KernelAttribute(
        "float",
        "Shortest wall-clock time measured so far for a full update step [seconds]",
        readonly=True,
    )
    max_update_time = KernelAttribute(
        "float",
        "Longest wall-clock time measured so far for a full update step [seconds]",
        readonly=True,
    )
    update_time_limit = KernelAttribute(
        "float",
        (
            "Maximum wall-clock time for one full update step [seconds]."
            + " This can be used to terminate simulations that slow down"
            + " significantly. Simulations may still get stuck if the slowdown"
            + " occurs within a single update step"
        ),
        default=float("+inf"),
    )

    _kernel_attr_names = set(
        k for k, v in vars().items() if isinstance(v, KernelAttribute)
    )
    _readonly_kernel_attrs = set(
        k for k, v in vars().items() if isinstance(v, KernelAttribute) and v._readonly
    )

    def set(self, **kwargs):
        return self.SetKernelStatus(kwargs)

    def get(self, *args):
        if len(args) == 0:
            return self.GetKernelStatus()
        if len(args) == 1:
            return self.GetKernelStatus(args[0])
        else:
            return self.GetKernelStatus(args)

    def __dir__(self):
        return list(set(vars(self).keys()) | set(self.__all__))


# Instantiate a NestModule to replace the nest Python module. Based on
# https://mail.python.org/pipermail/python-ideas/2012-May/014969.html
_module = NestModule(__name__)
# Manipulate the nest module instance through its `__dict__` (= vars())
_module_dict = vars(_module)
# Copy over the original module attributes to preverse all interpreter given
# magic attributes such as `__name__`, `__path__`, `__package__`, ...
_module_dict.update(_original_module_attrs)

# Import public APIs of submodules into the `nest.` namespace
_rel_import_star(_module_dict, ".lib.hl_api_connections")
_rel_import_star(_module_dict, ".lib.hl_api_exceptions")
_rel_import_star(_module_dict, ".lib.hl_api_info")
_rel_import_star(_module_dict, ".lib.hl_api_models")
_rel_import_star(_module_dict, ".lib.hl_api_nodes")
_rel_import_star(_module_dict, ".lib.hl_api_parallel_computing")
_rel_import_star(_module_dict, ".lib.hl_api_simulation")
_rel_import_star(_module_dict, ".lib.hl_api_spatial")
_rel_import_star(_module_dict, ".lib.hl_api_types")

# Finalize the nest module instance by generating its public API.
_api = list(k for k in _module_dict if not k.startswith("_"))
_api.extend(k for k in dir(NestModule) if not k.startswith("_"))
_module.__all__ = list(set(_api))

# Set the nest module object as the return value of `import nest` using sys
sys.modules[__name__] = _module

# Some compiled/binary components (`pynestkernel.pyx` for example) of NEST
# obtain a reference to this file's original module object instead of what's in
# `sys.modules`. For these edge cases we make available all attributes of the
# nest module instance to this file's module object.
globals().update(_module_dict)

# Clean up obsolete references
del _rel_import_star, _lazy_module_property, _module, _module_dict, \
    _original_module_attrs
