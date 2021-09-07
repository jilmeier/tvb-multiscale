# -*- coding: utf-8 -*-

import pickle  # dill

import numpy as np


def serialize_tvb_cosimulator(cosimulator):

    d = \
        {"integrator.dt": float(cosimulator.integrator.dt),
         "connectivity.number_of_regions": int(cosimulator.connectivity.number_of_regions),
         "connectivity.region_labels": np.copy(cosimulator.connectivity.region_labels),
         "connectivity.weights": np.copy(cosimulator.connectivity.weights),
         "connectivity.delays": np.copy(cosimulator.connectivity.delays),
         "coupling.a": np.copy(cosimulator.coupling.a),
         "model": str(cosimulator.model.__class__.__name__),
         "model.nvar": int(cosimulator.model.nvar),
         "model.nintvar": int(cosimulator.model.nintvar) if cosimulator.model.nintvar is not None else 0,
         "model.state_variables": list(cosimulator.model.state_variables),
         "model.cvar": np.copy(cosimulator.model.cvar),
         "monitor.period": float(cosimulator.monitors[0].period),
    }
    d["synchronization_time"] = float(getattr(cosimulator, "synchronization_time", d["integrator.dt"]))
    d["synchronization_n_step"] = float(getattr(cosimulator, "synchronization_n_step", 1))
    if hasattr(cosimulator.integrator, "noise"):
        d["integrator.noise.nsig"] = cosimulator.integrator.noise.nsig

    excluded_params = ("state_variables", "state_variable_range", "state_variable_boundaries", "variables_of_interest",
                       "nvar", "nintvar", "cvar", "noise", "psi_table", "nerf_table", "gid")
    for param in type(cosimulator.model).declarative_attrs:
        if param in excluded_params:
            continue
        d["model.%s" % param] = np.copy(getattr(cosimulator.model, param))

    return d


def dump_serial_tvb_cosimulator(serial_tvb_cosim, filepath):
    with open(filepath, "wb") as f:
        pickle.dump(serial_tvb_cosim, f)  # dill


def load_serial_tvb_cosimulator(filepath):
    with open(filepath, "rb") as f:
        serial_tvb_cosim = pickle.load(f)  # dill
    return serial_tvb_cosim

