# sweeps.py
#
# This file is part of scqubits.
#
#    Copyright (c) 2019 and later, Jens Koch and Peter Groszkowski
#    All rights reserved.
#
#    This source code is licensed under the BSD-style license found in the
#    LICENSE file in the root directory of this source tree.
############################################################################

import functools
import itertools

from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

import scqubits.core.storage as storage
import scqubits.core.sweep_observables as observable
import scqubits.settings as settings
import scqubits.utils.misc as utils
import scqubits.utils.spectrum_utils as spec_utils

from scqubits import Oscillator
from scqubits.core.namedslots_array import NamedSlotsNdarray

if TYPE_CHECKING:
    from scqubits import HilbertSpace, Oscillator, SpectrumData
    from scqubits.core.qubit_base import QubitBaseClass
    from scqubits.core.param_sweep import ParameterSweep, ParameterSweepBase

    QuantumSys = Union[QubitBaseClass, Oscillator]


if settings.IN_IPYTHON:
    from tqdm.notebook import tqdm
else:
    from tqdm import tqdm


def generator(sweep: "ParameterSweepBase", func: callable, **kwargs) -> np.ndarray:
    """Method for computing custom data as a function of the external parameter,
    calculated via the function `func`.

    Parameters
    ----------
    sweep:
        ParameterSweep object containing HilbertSpace and spectral information
    func:
        signature: `func(parametersweep, [paramindex_tuple, paramvals_tuple,
        **kwargs])`, specifies how to calculate the data for a single choice of
        parameter(s)
    **kwargs:
        keyword arguments to be included in func

    Returns
    -------
        array of custom data
    """
    reduced_parameters = sweep.parameters.create_sliced(
        sweep._current_param_indices, remove_fixed=False
    )
    total_count = np.prod(reduced_parameters.counts)

    def func_effective(paramindex_tuple: Tuple[int], params, **kw) -> Any:
        paramvals_tuple = params[paramindex_tuple]
        return func(
            sweep,
            paramindex_tuple=paramindex_tuple,
            paramvals_tuple=paramvals_tuple,
            **kw,
        )

    if hasattr(func, "__name__"):
        func_name = func.__name__
    else:
        func_name = ""

    data_array = list(
        tqdm(
            map(
                functools.partial(
                    func_effective,
                    params=reduced_parameters,
                    **kwargs,
                ),
                itertools.product(*reduced_parameters.ranges),
            ),
            total=total_count,
            desc="sweeping " + func_name,
            leave=False,
            disable=settings.PROGRESSBAR_DISABLED,
        )
    )
    data_array = np.asarray(data_array)
    return data_array.reshape(reduced_parameters.counts)
