# -*- coding: utf-8 -*-

from logging import Logger
from enum import Enum

from tvb.basic.neotraits.api import HasTraits, Attr, List

from tvb_multiscale.core.interfaces.tvb.builders import TVBSpikeNetInterfaceBuilder
from tvb_multiscale.core.interfaces.spikeNet.interfaces import TVBtoSpikeNetModels, SpikeNetToTVBModels
from tvb_multiscale.core.interfaces.spikeNet.builders import \
    SpikeNetRemoteInterfaceBuilder, SpikeNetTransformerInterfaceBuilder,  \
    SpikeNetOutputTransformerInterfaceBuilder, SpikeNetInputTransformerInterfaceBuilder
from tvb_multiscale.core.spiking_models.builders.factory import build_and_connect_devices

from tvb_multiscale.tvb_nest.config import Config, CONFIGURED, initialize_logger
from tvb_multiscale.tvb_nest.interfaces.interfaces import \
    NESTOutputInterfaces, NESTInputInterfaces, \
    NESTSenderInterface, NESTReceiverInterface, \
    NESTTransformerSenderInterface, NESTReceiverTransformerInterface, \
    TVBtoNESTInterfaces, NESTtoTVBInterfaces, \
    TVBtoNESTInterface, NESTtoTVBInterface
from tvb_multiscale.tvb_nest.interfaces.io import NESTSpikeRecorderSet, \
    NESTSpikeGeneratorSet, NESTInhomogeneousPoissonGeneratorSet, NESTStepCurrentGeneratorSet, \
    NESTParrotSpikeGeneratorSet, NESTParrotInhomogeneousPoissonGeneratorSet
from tvb_multiscale.tvb_nest.nest_models.network import NESTNetwork
from tvb_multiscale.tvb_nest.nest_models.builders.nest_factory import create_device, connect_device


TVBtoNESTModels = TVBtoSpikeNetModels
NESTtoTVBModels = SpikeNetToTVBModels


class DefaultTVBtoNESTModels(Enum):
    RATE = "RATE_TO_SPIKES"
    SPIKES = "PARROT_SPIKES"
    CURRENT = "CURRENT"


class DefaultNESTtoTVBModels(Enum):
    SPIKES = "SPIKES"


class NESTInputProxyModels(Enum):
    RATE = NESTInhomogeneousPoissonGeneratorSet
    RATE_TO_SPIKES = NESTParrotInhomogeneousPoissonGeneratorSet
    SPIKES = NESTSpikeGeneratorSet
    PARROT_SPIKES = NESTParrotSpikeGeneratorSet
    CURRENT = NESTStepCurrentGeneratorSet


class NESTOutputProxyModels(Enum):
    SPIKES = NESTSpikeRecorderSet


class NESTInterfaceBuilder(HasTraits):

    """NESTInterfaceBuilder class"""

    _tvb_to_spikeNet_models = TVBtoNESTModels
    _spikeNet_to_tvb_models = NESTtoTVBModels

    config = Attr(
        label="Configuration",
        field_type=Config,
        doc="""Configuration class instance.""",
        required=True,
        default=CONFIGURED
    )

    logger = Attr(
        label="Logger",
        field_type=Logger,
        doc="""logging.Logger instance.""",
        required=True,
        default=initialize_logger(__name__, config=CONFIGURED)
    )

    spiking_network = Attr(label="NEST Network",
                           doc="""The instance of NESTNetwork class""",
                           field_type=NESTNetwork,
                           required=True)

    output_interfaces = List(of=dict, default=(), label="Output interfaces configurations",
                             doc="List of dicts of configurations for the output interfaces to be built")

    input_interfaces = List(of=dict, default=(), label="Input interfaces configurations",
                            doc="List of dicts of configurations for the input interfaces to be built")

    @property
    def nest_network(self):
        return self.spiking_network

    @property
    def nest_instance(self):
        return self.spiking_network.nest_instance

    @property
    def spikeNet_min_delay(self):
        return self.nest_instance.GetKernelStatus("min_delay")

    @property
    def nest_min_delay(self):
        return self.nest_instance.GetKernelStatus("min_delay")

    def _build_and_connect_devices(self, interface, **kwargs):
        return build_and_connect_devices(interface, create_device, connect_device,
                                         self.spiking_network.brain_regions,
                                         self.config, nest_instance=self.nest_instance, **kwargs)

    def _default_receptor_type(self, source_node, target_node):
        return 0

    @property
    def _default_min_delay(self):
        return self.nest_min_delay


class NESTRemoteInterfaceBuilder(NESTInterfaceBuilder, SpikeNetRemoteInterfaceBuilder):

    """NESTRemoteInterfaceBuilder class"""

    _default_tvb_to_nest_models = DefaultTVBtoNESTModels
    _default_nest_to_tvb_models = DefaultNESTtoTVBModels

    _input_proxy_models = NESTInputProxyModels
    _output_proxy_models = NESTOutputProxyModels

    _output_interfaces_type = NESTOutputInterfaces
    _input_interfaces_type = NESTInputInterfaces

    _output_interface_type = NESTSenderInterface
    _input_interface_type = NESTReceiverInterface

    def configure(self):
        NESTInterfaceBuilder.configure(self)
        SpikeNetRemoteInterfaceBuilder.configure(self)


class NESTTransformerInterfaceBuilder(NESTInterfaceBuilder, SpikeNetTransformerInterfaceBuilder):

    """NESTTransformerInterfaceBuilder class"""

    _input_proxy_models = NESTInputProxyModels
    _output_proxy_models = NESTOutputProxyModels

    _output_interfaces_type = NESTOutputInterfaces
    _input_interfaces_type = NESTInputInterfaces

    _output_interface_type = NESTTransformerSenderInterface
    _input_interface_type = NESTReceiverTransformerInterface

    def configure(self):
        NESTInterfaceBuilder.configure(self)
        SpikeNetTransformerInterfaceBuilder.configure(self)


class NESTOutputTransformerInterfaceBuilder(NESTInterfaceBuilder, SpikeNetOutputTransformerInterfaceBuilder):

    """NESTOutputTransformerInterfaceBuilder class"""

    _input_proxy_models = NESTInputProxyModels
    _output_proxy_models = NESTOutputProxyModels

    _output_interfaces_type = NESTOutputInterfaces
    _input_interfaces_type = NESTInputInterfaces

    _output_interface_type = NESTTransformerSenderInterface
    _input_interface_type = NESTReceiverInterface

    def configure(self):
        NESTInterfaceBuilder.configure(self)
        SpikeNetOutputTransformerInterfaceBuilder.configure(self)


class NESTInputTransformerInterfaceBuilder(NESTInterfaceBuilder, SpikeNetInputTransformerInterfaceBuilder):

    """NESTInputTransformerInterfaceBuilder class"""

    _input_proxy_models = NESTInputProxyModels
    _output_proxy_models = NESTOutputProxyModels

    _output_interfaces_type = NESTOutputInterfaces
    _input_interfaces_type = NESTInputInterfaces

    _output_interface_type = NESTSenderInterface
    _input_interface_type = NESTReceiverTransformerInterface

    def configure(self):
        NESTInterfaceBuilder.configure(self)
        SpikeNetInputTransformerInterfaceBuilder.configure(self)


class TVBNESTInterfaceBuilder(NESTInterfaceBuilder, TVBSpikeNetInterfaceBuilder):

    """TVBNESTInterfaceBuilder class"""

    _tvb_to_spikeNet_models = TVBtoNESTModels
    _spikeNet_to_tvb_models = NESTtoTVBModels

    _default_nest_to_tvb_models = DefaultNESTtoTVBModels
    _default_tvb_to_nest_models = DefaultTVBtoNESTModels

    _input_proxy_models = NESTOutputProxyModels  # Input to SpikeNet is output of TVB
    _output_proxy_models = NESTInputProxyModels  # Output of SpikeNet is input to TVB

    _output_interfaces_type = TVBtoNESTInterfaces
    _input_interfaces_type = NESTtoTVBInterfaces

    _output_interface_type = TVBtoNESTInterface
    _input_interface_type = NESTtoTVBInterface

    def configure(self):
        NESTInterfaceBuilder.configure(self)
        TVBSpikeNetInterfaceBuilder.configure(self)
