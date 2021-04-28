# -*- coding: utf-8 -*-

from six import string_types
from collections import OrderedDict

import pandas as pd
import xarray as xr
import numpy as np

from tvb_multiscale.core.config import initialize_logger, LINE

from tvb.basic.neotraits.api import HasTraits, Int

from tvb.contrib.scripts.utils.log_error_utils import raise_value_error
from tvb.contrib.scripts.utils.data_structures_utils import series_loop_generator, is_integer


LOG = initialize_logger(__name__)


class SpikingNodesSet(pd.Series, HasTraits):

    """SpikingNodesSet class is an indexed mapping
       (based on inheriting from pandas.Series class)
       between SpikingNodesCollections labels and contents
       residing at a specific brain node's set.
    """

    _number_of_nodes = Int(field_type=int, default=0, required=True, label="Number of nodes",
                           doc="""The number of nodes of SpikingNodesSet """)

    _collection_name = "Population"
    
    def __init__(self, nodes=None, **kwargs):
        name = kwargs.pop("label", kwargs.pop("name", ""))
        pd.Series.__init__(self, nodes, name=name, **kwargs)
        self._number_of_nodes = self.get_number_of_nodes()
        HasTraits.__init__(self)

    @property
    def spiking_simulator_module(self):
        for i_n, nod_lbl, nodes in self._loop_generator():
            if nodes.spiking_simulator_module is not None:
                return nodes.spiking_simulator_module
        return None

    def __repr__(self):
        return "%s - Label: %s\n%ss: %s" % (self.__class__.__name__, self.label,
                                            self._collection_name,  str(self.collections))

    def __str__(self):
        return self.print_str()

    def print_str(self, connectivity=False):
        output = self.__repr__() + "%ss:\n" % self._collection_name
        for pop in self.collections:
            output += LINE + self[pop].print_str(connectivity)
        return output

    def __len__(self):
        return pd.Series.__len__(self)

    def __getitem__(self, items):
        """If the argument is a sequence, a new SpikingNodesSet instance is returned.
           If the argument is an integer index or a string label index,
           the corresponding SpikingNodeCollection is returned.
        """
        pops = pd.Series.__getitem__(self, items)
        if isinstance(items, string_types) or is_integer(items):
            return pops
        return self.__class__(nodes=pops, label=self.label)

    @property
    def label(self):
        """The node's set label."""
        return self.name

    # Methods to get or set attributes for nodes and/or their connections:

    def _loop_generator(self, inds_or_lbls=None):
        """Method to create a generator looping through the SpikingNodeCollection objects
          and returning the indice, the label, and the SpikingNodeCollection itself.
            Arguments:
             inds_or_lbls: collection (list, tuple, array) of the indices or keys of selected collections.
             Default = None, corresponds to all collections of the node's set.
            Returns:
             The generator object
         """
        return series_loop_generator(self, inds_or_lbls)

    def get_nodes(self, inds_or_lbls=None):
        """Method to get the nodes indices of the SpikingNodesSet's collections.
           Argument:
            inds_or_lbls: collection (list, tuple, array) of the indices or keys of selected collections.
                              Default = None, corresponds to all collections of the SpikingNodesSet.
           Returns:
            tuple of nodes."""
        output = ()
        for id, lbl, nodes in self._loop_generator(inds_or_lbls):
            output += tuple(nodes.nodes)
        return output

    def get_number_of_nodes(self, inds_or_lbls=None):
        return len(self.get_nodes(inds_or_lbls))

    def get_number_of_nodes_per_collection(self, inds_or_lbls=None):
        output = []
        labels = []
        for id, lbl, nodes in self._loop_generator(inds_or_lbls):
            labels.append(nodes)
            output.append(nodes.get_size())
        return xr.DataArray(np.array(output),
                            dims=[self._collection_name], coords={self._collection_name: np.array(labels)})

    def Set(self, values_dict, inds_or_lbls=None):
        """Method to set attributes of the SpikingNodesSet's collections' nodes.
           Arguments:
            values_dict: dictionary of attributes names' and values.
            inds_or_lbls: collection (list, tuple, array) of the indices or keys of selected collections.
                          Default = None, corresponds to all collections of the set.
        """
        for id, lbl, pop in self._loop_generator(inds_or_lbls):
            pop.Set(values_dict)

    def Get(self, attrs=None, inds_or_lbls=None, summary=False):
        """Method to get attributes of the SpikingNodesSet's collections' nodes.
           Arguments:
            attrs: names of attributes to be returned. Default = None, corresponds to all nodes' attributes.
            inds_or_lbls: collection (list, tuple, array) of the indices or keys of selected collections.
                             Default = None, corresponds to all collections of the node's set.
            summary: if integer, return a summary of unique output values
                                 within accuracy of the specified number of decimal digits
                     otherwise, if it is not None or False return
                     either a dictionary of a statistical summary of mean, minmax, and variance for numerical attributes,
                     or a list of unique string entries for all other attributes,
                     Default = None, corresponds to returning all values
           Returns:
            Series of collections' nodes' attributes.
        """
        output = pd.Series()
        for id, lbl, nodes in self._loop_generator(inds_or_lbls):
            output[lbl] = nodes.Get(attrs, summary=summary)
        return output

    def get_attributes(self, inds_or_lbls=None, summary=False):
        """Method to get all attributes of the SpikingNodesSet's collections' nodes.
           Arguments:
            inds_or_lbls: collection (list, tuple, array) of the indices or keys of selected collections.
                             Default = None, corresponds to all collections of the node's set.
            summary: if integer, return a summary of unique output values
                                 within accuracy of the specified number of decimal digits
                     otherwise, if it is not None or False return
                     either a dictionary of a statistical summary of mean, minmax, and variance for numerical attributes,
                     or a list of unique string entries for all other attributes,
                     Default = None, corresponds to returning all values
           Returns:
            Series of collections' nodes' attributes.
        """
        return self.Get(inds_or_lbls=inds_or_lbls, summary=summary)

    def GetConnections(self, inds_or_lbls=None, source_or_target=None):
        """Method to get the connections of the SpikingNodesSet's collections.
           Argument:
            inds_or_lbls: collection (list, tuple, array) of the indices or keys of selected collections.
                              Default = None, corresponds to all collections of the SpikingNodesSet.
            source_or_target: Direction of connections relative to the region's nodes
                              "source", "target" or None (Default; corresponds to both source and target)
           Returns:
            Series of connections.
        """
        output = pd.Series()
        for id, lbl, nodes in self._loop_generator(inds_or_lbls):
            output[lbl] = nodes.GetConnections(source_or_target=source_or_target)
        return output

    def SetToConnections(self, values_dict, inds_or_lbls=None, source_or_target=None):
        """Method to set attributes of the connections from/to the SpikingNodesSet's collections.
           Arguments:
            values_dict: dictionary of attributes names' and values.
            inds_or_lbls: collection (list, tuple, array) of the indices or keys of selected collections.
                              Default = None, corresponds to all collections of the SpikingNodesSet.
            source_or_target: Direction of connections relative to the set's nodes
                              "source", "target" or None (Default; corresponds to both source and target)
        """
        for id, lbl, nodes in self._loop_generator(inds_or_lbls):
            nodes.SetToConnections(values_dict, source_or_target=source_or_target)

    def GetFromConnections(self, attrs=None, inds_or_lbls=None, source_or_target=None, summary=None):
        """Method to get attributes of the connections from/to the SpikingNodesSet's collections.
           Arguments:
            attrs: collection (list, tuple, array) of the attributes to be included in the output.
            inds_or_lbls: collection (list, tuple, array) of the indices or keys of selected collections.
                              Default = None, corresponds to all collections of the SpikingNodesSet.
            source_or_target: Direction of connections relative to the set's nodes
                              "source", "target" or None (Default; corresponds to both source and target)
            summary: if integer, return a summary of unique output values
                                 within accuracy of the specified number of decimal digits
                     otherwise, if it is not None or False return
                     either a dictionary of a statistical summary of mean, minmax, and variance for numerical attributes,
                     or a list of unique string entries for all other attributes,
                     Default = None, corresponds to returning all values
           Returns:
            Series of connections' attributes.
        """
        output = pd.Series()
        for id, lbl, nodes in self._loop_generator(inds_or_lbls):
            output[lbl] = nodes.GetFromConnections(attrs, source_or_target=source_or_target, summary=summary)
        return output

    def get_weights(self, inds_or_lbls=None, source_or_target=None, summary=None):
        """Method to get the connections' weights of the SpikingNodesSet's nodes.
           Argument:
            inds_or_lbls: collection (list, tuple, array) of the indices or keys of selected collections.
                              Default = None, corresponds to all collections of the SpikingNodesSet.
            source_or_target: Direction of connections relative to the set's nodes
                              "source", "target" or None (Default; corresponds to both source and target)
            summary: if integer, return a summary of unique output values
                                 within accuracy of the specified number of decimal digits
                     otherwise, if it is not None or False return
                     either a dictionary of a statistical summary of mean, minmax, and variance for numerical attributes,
                     or a list of unique string entries for all other attributes,
                     Default = None, corresponds to returning all values
           Returns:
            Series of collections' nodes' weights.
        """
        return self.GetFromConnections(self._weight_attr, inds_or_lbls, source_or_target, summary)

    def get_delays(self, inds_or_lbls=None, source_or_target=None, summary=None):
        """Method to get the connections' delays of the SpikingNodesSet's nodes.
           Argument:
            inds_or_lbls: collection (list, tuple, array) of the indices or keys of selected collections.
                              Default = None, corresponds to all collections of the SpikingNodesSet.
            source_or_target: Direction of connections relative to the nodes's nodes
                              "source", "target" or None (Default; corresponds to both source and target)
            summary: if integer, return a summary of unique output values
                                 within accuracy of the specified number of decimal digits
                     otherwise, if it is not None or False return
                     either a dictionary of a statistical summary of mean, minmax, and variance for numerical attributes,
                     or a list of unique string entries for all other attributes,
                     Default = None, corresponds to returning all values
           Returns:
            Series of collections' nodes' delays.
        """
        return self.GetFromConnections(self._delay_attr, inds_or_lbls, source_or_target, summary)

    def get_receptors(self, inds_or_lbls=None, source_or_target=None, summary=None):
        """Method to get the connections' receptors of the SpikingNodesSet's nodes.
           Argument:
            inds_or_lbls: collection (list, tuple, array) of the indices or keys of selected collections.
                               Default = None, corresponds to all collections of the SpikingNodesSet.
            source_or_target: Direction of connections relative to the nodes's nodes
                              "source", "target" or None (Default; corresponds to both source and target)
            summary: if integer, return a summary of unique output values
                                 within accuracy of the specified number of decimal digits
                     otherwise, if it is not None or False return
                     either a dictionary of a statistical summary of mean, minmax, and variance for numerical attributes,
                     or a list of unique string entries for all other attributes,
                     Default = None, corresponds to returning all values
           Returns:
            Series of collections' nodes' receptors.
        """
        return self.GetFromConnections(self._receptor_attr, inds_or_lbls, source_or_target, summary)

    @property
    def collections(self):
        """Method to get the list of collections' labels of the SpikingNodesSet.
           Returns:
            list of collections' labels.
        """
        return list(self.index)

    @property
    def nodes(self):
        """Method to get the nodes of the SpikingNodesSet's collections.
           Returns:
            tuple of nodes."""
        return self.get_nodes()

    @property
    def number_of_nodes(self):
        """Method to get the total number of nodes of the SpikingNodesSet's collections,
           and for setting the respective protected property."""
        if self._number_of_nodes is None or self._number_of_nodes == 0:
            self._number_of_nodes = self.get_number_of_nodes()
        return self._number_of_nodes

    @property
    def number_of_nodes_per_collection(self):
        return self.get_number_of_nodes_per_collection()

    @property
    def attributes(self):
        return self.get_attributes()

    @property
    def connections(self):
        """Method to get the connections of the SpikingNodesSet's nodes.
           Returns:
            Series of connections.
        """
        return self.GetConnections()

    @property
    def weights(self):
        """Method to get the connections' weights of the SpikingNodesSet's nodes.
           Returns:
            Series of collections' nodes' weights.
        """
        return self.get_weights()

    @property
    def delays(self):
        """Method to get the connections' delays of the SpikingNodesSet's nodes.
           Returns:
            Series of collections' nodes' delays.
        """
        return self.get_delays()

    @property
    def receptors(self):
        """Method to get the connections' receptors of the SpikingNodesSet's nodes.
           Returns:
            Series of collections' nodes' receptors.
        """
        return self.get_receptors()

    def _return_by_type(self, values_dict, return_type="dict", concatenation_index_name=None, name=None):
        """This method returns data collected from the SpikingNodeCollections of the SpikingNodesSet
           in a desired output format, among dict (Default), pandas.Series, xarray.DataArray or a list of values,
           depending on user input.
           Arguments:
            values_dict: dictionary of attributes and values
            return_type: string selecting one of the return types ["values", "dict", "Series", "DataArray"].
                         Default = "dict". "values" stands for a list of values, without labelling the output.
            concatenation_index_name: The dimension name along which the concatenation across devices happens.
                                      Default =None, defaults to _collection_name.
            name: Label of the output data. Default = None.
           Returns:
            output data in the selected type.
        """
        if not isinstance(concatenation_index_name, string_types):
            concatenation_index_name = self._collection_name
        if return_type == "values":
            return list(values_dict.values())
        elif return_type == "dict":
            return values_dict
        elif return_type == "Series":
            return pd.Series(values_dict, name=name)
        elif return_type == "DataArray":
            if name is None:
                name = self.name
            for key, val in values_dict.items():
                if isinstance(val, xr.DataArray):
                    val.name = key
                else:
                    raise_value_error("DataArray concatenation not possible! "
                                      "Not all outputs are DataArrays!:\n %s" % str(values_dict))
            dims = list(values_dict.keys())
            values = list(values_dict.values())
            if len(values) == 0:
                return xr.DataArray([])
            output = xr.concat(values, dim=pd.Index(dims, name=concatenation_index_name))
            output.name = name
            return output
        else:
            return values_dict

    def do_for_all(self, attr, *args, nodes=None, return_type="values",
                   concatenation_index_name=None, name=None, **kwargs):
        """This method will perform the required action (SpikingNodeCollection method or property), and
            will return the output data collected from (a subset of) the SpikingNodeCollections of the SpikingNodesSet,
            in a desired output format, among dict (Default), pandas.Series, xarray.DataArray or a list of values,
           depending on user input.
           Arguments:
            attr: the name of the method/property of SpikingNodeCollection requested
            *args: possible position arguments of attr
            nodes: a subselection of Device nodes of the SpikingNodesSet the action should be performed upon
            return_type: string selecting one of the return types ["values", "dict", "Series", "DataArray"].
                         Default = "values". "values" stands for a list of values, without labelling the output.
            concatenation_index_name: The dimension name along which the concatenation across devices happens.
                                      Default = None, which defaults to _collection_name.
            name: Label of the output data. Default = None.
            **kwargs: possible keyword arguments of attr
           Returns:
            output data in the selected type.
        """
        values_dict = OrderedDict()
        for device in self.devices(nodes):
            val = getattr(self[device], attr)
            if hasattr(val, "__call__"):
                values_dict.update({device: val(*args, **kwargs)})
            else:
                values_dict.update({device: val})
        return self._return_by_type(values_dict, return_type, concatenation_index_name, name)