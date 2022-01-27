# -*- coding: utf-8 -*-

from inspect import stack
from itertools import product
from collections import OrderedDict
from six import string_types
from enum import Enum

import numpy as np
from scipy.stats import describe
import pandas as pd
from xarray import DataArray


from tvb.contrib.scripts.utils.data_structures_utils import \
    ensure_list, flatten_list, is_integer, extract_integer_intervals


def is_iterable(obj):
    try:
        iter(obj)
        return True
    except:
        return False


def get_caller_fun_name(caller_id=1):
    return str(stack()[caller_id][3])


def get_ordered_dimensions(dims, dims_order):
    out_dims = []
    dims = ensure_list(dims)
    for dim in dims_order:
        if dim in dims:
            out_dims.append(dim)
            dims.remove(dim)
    return out_dims + dims


def flatten_neurons_inds_in_DataArray(data_array, neurons_dim_label="Neuron"):
    dims = list(data_array.dims)
    try:
        dim_id = dims.index(neurons_dim_label)
    except:
        dim_id = -1
    neurons_dim_label = dims[dim_id]
    neuron_labels = np.arange(data_array.shape[dim_id])
    data_array.coords[neurons_dim_label] = neuron_labels
    return data_array


def filter_events(events, variables=None, times=None, exclude_times=[]):
    """This method will select/exclude part of the measured events, depending on user inputs
        Arguments:
            events: dictionary of events
            variables: sequence (list, tuple, array) of variables to be included in the output,
                       assumed to correspond to keys of the events dict.
                       Default=None, corresponds to all keys of events.
            times: sequence (list, tuple, array) of times the events of which should be included in the output.
                     Default = None, corresponds to all events' times.
            exclude_times: sequence (list, tuple, array) of times
                             the events of which should be excluded from the output. Default = [].
        Returns:
              the filtered dictionary (of arrays per attribute) of events
    """

    def in_fun(values):
        # Function to return a boolean about whether a value is
        # within a sequence or an interval (len(values) == 2) of values:
        if len(values) == 2:
            if values[0] is not None:
                if values[1] is not None:
                    return lambda x: x >= values[0] and x <= values[1]
                else:
                    return lambda x: x >= values[0]
            elif values[1] is not None:
                return lambda x: x <= values[0]
            else:
                return lambda x: x
        else:
            return lambda x: x in values

    # The variables to return:
    if variables is None:
        variables = events.keys()

    # The events:
    output_events = OrderedDict()

    events_times = np.array(events["times"])

    n_events = len(events["times"])
    if n_events > 0:
        # As long as there are events:
        # If we (un)select times...
        if times is not None and len(times) > 0:
            in_times = in_fun(flatten_list(times))
        else:
            in_times = lambda x: True
        if exclude_times is not None and len(exclude_times) > 0:
            not_in_exclude_times = lambda x: not in_fun(flatten_list(exclude_times))(x)
        else:
            not_in_exclude_times = lambda x: True
        inds = np.logical_and(np.ones((n_events,)),
                              [in_times(time) and not_in_exclude_times(time)
                               for time in events_times])
        for var in ensure_list(variables):
            output_events[var] = events[var][inds]
    else:
        for var in ensure_list(variables):
            output_events[var] = np.array([])
    return output_events


def summarize(results, digits=None):

    def unique(values, astype=None):
        if len(values):
            if astype is None:
                astype = str(np.array(values).dtype)
            try:
                return pd.unique(vals).astype(astype)
            except:
                return np.unique(vals).astype(astype)
        else:
            return np.array(values)

    def unique_dicts(list_of_dicts):
        return [dict(t) for t in {tuple(d.items()) for d in list_of_dicts}]

    def unique_floats_fun(vals):
        scale = 10 ** np.floor(np.log10(np.percentile(np.abs(vals), 95)))
        return scale * unique(np.around(vals / scale, decimals=digits))

    def stats_fun(vals):
        d = describe(vals)
        summary = {}
        summary["n"] = d.nobs
        summary["mean"] = d.mean
        summary["minmax"] = d.minmax
        summary["var"] = d.variance
        return summary

    output = {}
    for attr, val in results.items():
        vals = ensure_list(val)
        try:
            val_type = str(np.array(vals).dtype)
            if np.all([isinstance(val, dict) for val in vals]):
                # If they are all dicts:
                output[attr] = np.array(unique_dicts(vals))
            elif isinstance(vals[0], string_types) \
                    or val_type[0] == "i" or val_type[0] == "b" or val_type[0] == "o" or val_type[:2] == "<U":
                # String, integer or boolean values
                unique_vals = list(unique(vals, val_type))
                n_unique_vals = len(unique_vals)
                if n_unique_vals < 2:
                    # If they are all of the same value, just set this value:
                    output[attr] = np.array(unique_vals[0])
                elif n_unique_vals <= 10:
                    # Otherwise, return a summary dictionary with the indices of each value:
                    output[attr] = OrderedDict()
                    vals = np.array(vals)
                    for unique_val in unique_vals:
                        output[attr][unique_val] = extract_integer_intervals(np.where(vals == unique_val)[0])
                else:
                    if val_type[0] == "i":
                        output[attr] = extract_integer_intervals(vals)
                    else:
                        output[attr] = unique_vals
            else:  # Assuming floats or arbitrary objects...
                unique_vals = unique(vals)
                if len(unique_vals) > 3:
                    # If there are more than three different values, try to summarize them...
                    try:
                        if is_integer(digits):
                            output[attr] = unique_floats_fun(unique_vals)
                        else:
                            output[attr] = stats_fun(np.array(vals))
                    except:
                        output[attr] = unique_vals
                else:
                    if len(unique_vals) == 1:
                        output[attr] = unique_vals[0]
                    output[attr] = unique_vals
        except:
            # Something went wrong, return the original property
            output[attr] = np.array(vals)
    return output


def cross_dimensions_and_coordinates_MultiIndex(dims, pop_labels, all_regions_lbls):
    from pandas import MultiIndex
    stacked_dims = "-".join(dims)
    names = []
    new_dims = []
    for d in ["i", "j"]:
        names.append([dim + "_" + d for dim in dims])
        new_dims.append(stacked_dims + "_" + d)
    new_coords = {new_dims[0]: MultiIndex.from_product([pop_labels, all_regions_lbls], names=names[0]),
                  new_dims[1]: MultiIndex.from_product([pop_labels, all_regions_lbls], names=names[1])}
    return new_dims, new_coords


def combine_DataArray_dims(arr, dims_combinations, join_string=", ", return_array=True):
    new_dims = []
    new_coords = {}
    stacked_dims = {}
    for dim_combin in dims_combinations:
        new_dim = join_string.join(["%s" % arr.dims[i_dim] for i_dim in dim_combin])
        new_dims.append(new_dim)
        stacked_dims[new_dim] =[arr.dims[i_dim] for i_dim in dim_combin]
        new_coords[new_dim] = [join_string.join(coord_combin)
                               for coord_combin in product(*[arr.coords[arr.dims[i_dim]].data for i_dim in dim_combin])]
    if return_array:
        return DataArray(arr.stack(**stacked_dims).data, dims=new_dims, coords=new_coords, name=arr.name)
    else:
        return arr.stack(**stacked_dims).data, new_dims, new_coords


def get_enum_names(en):
    return [val.name for val in en.__members__.values()]


def get_enum_values(en):
    return [val.value for val in en.__members__.values()]


def combine_enums(enum_name, *args):
    d = OrderedDict()
    for enm in args:
        for name, member in enm.__members__.items():
            d[name] = member.value
    return Enum(enum_name, d)


def trait_object_str(class_name, summary):
    result = ['{} ('.format(class_name)]
    maxlenk = max(len(k) for k in summary)
    for k in summary:
        result.append('  {:.<{}} {}'.format(k + ' ', maxlenk, summary[k]))
    result.append(')')
    return '\n'.join(result)
