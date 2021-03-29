# -*- coding: utf-8 -*-

from copy import deepcopy
from abc import ABCMeta, abstractmethod

import numpy as np

from tvb.basic.neotraits.api import HasTraits, Attr, Float, NArray, List

from tvb_multiscale.core.config import CONFIGURED


class Transformer(HasTraits):
    __metaclass__ = ABCMeta

    """
        Abstract Transformer base class comprising:
            - an input buffer data,
            - an output buffer data,
            - an abstract method for the computations applied 
              upon the input buffer data for the output buffer data to result.
    """

    input_buffer = []

    output_buffer = []

    dt = Float(label="Time step",
               doc="Time step of simulation",
               required=True,
               default=0.1)

    input_time = NArray(
        dtype=np.int,
        label="Input time vector",
        doc="""Buffer of time (float) or time steps (integer) corresponding to the input buffer.""",
        required=True,
        default=np.array([]).astype("i")
    )

    output_time = NArray(
        dtype=np.int,
        label="Output time vector",
        doc="""Buffer of time (float) or time steps (integer) corresponding to the output bufer.""",
        required=True,
        default=np.array([]).astype("i")
    )

    def compute_time(self):
        self.output_time = np.copy(self.input_time)

    @abstractmethod
    def compute(self, *args, **kwargs):
        """Abstract method for the computation on the input buffer data for the output buffer data to result."""
        pass

    def __call__(self):
        self.compute_time()
        self.compute()

    def _assert_size(self, attr, buffer="input", dim=0):
        value = getattr(self, attr)
        buffer_size = len(getattr(self, "%s_buffer" % buffer))
        if buffer_size != 0:
            if buffer_size != value.shape[dim]:
                if value.shape[dim] == 1:
                    value = np.repeat(value, buffer_size, axis=dim)
                else:
                    raise ValueError("%s (=%s) is neither of length 1 "
                                     "nor of length equal to the proxy dimension (%d) of the buffer (=%d)"
                                     % (attr, str(value), dim, buffer_size))
                setattr(self, attr, value)
        return value

    def print_str(self):
        output = "\n%s, dt = %g" % (self.__repr__(), self.dt)
        if self.receiver:
            output += "\nReceiver: %s" % str(self.receiver)
        if self.sender:
            output += "\nSender: %s" % str(self.sender)


# A few basic examples:


class Elementary(Transformer):
    """
        Elementary Transformer just copies the input to the output without any computation.
        It comprises of:
            - an input buffer data numpy.array,
            - an output buffer data numpy.array,
            - a method to copy the input buffer data to the output buffer.
    """

    def compute(self):
        """Method that just copies input buffer data to the output buffer"""
        self.output_buffer = deepcopy(self.input_buffer)


class Scale(Transformer):
    """
        Scale Transformer scales the input with a scale factor in order to compute the output.
        It comprises of:
            - an input buffer data numpy.array,
            - an output buffer data numpy.array,
            - a scale factor numpy.array,
            - a method to multiply the input buffer data by the scale factor for the output buffer data to result.
    """

    scale_factor = NArray(
        label="Scale factor",
        doc="""Array to scale input buffer.""",
        required=True,
        default=np.array([1.0])
    )

    @property
    def _scale_factor(self):
        return self._assert_size("scale_factor")

    def configure(self):
        super(Scale, self).configure()
        self._scale_factor

    def compute(self):
        """Method that just scales input buffer data to compute the output buffer data."""
        if isinstance(self.input_buffer, np.ndarray):
            self.output_buffer = self.scale_factor * self.input_buffer
        else:
            self.output_buffer = []
            for scale_factor, input_buffer in zip(self._scale_factor, self.input_buffer):
                self.output_buffer.append(scale_factor * input_buffer)


class ScaleRate(Scale):

    """ScaleRate class that just scales mean field rates to spiking rates,
       including any unit conversions and conversions from mean field to total rates"""

    pass


class ScaleCurrent(Scale):
    """ScaleCurrent class that just scales mean field currents to spiking network ScaleCurrent,
       including any unit conversions and conversions from mean field to total rates"""

    pass


class DotProduct(Transformer):
    """
        DotProduct Transformer computes the dot product of the input with a scale factor
        in order to compute the output.
        It comprises of:
            - an input buffer data numpy.array,
            - an output buffer data numpy.array,
            - a dot factor numpy.array,
            - a method to perform the left dot product upon the input buffer for the output buffer data to result.
    """

    input_buffer = NArray(
        label="Input buffer",
        doc="""Array to store temporarily the data to be transformed.""",
        required=True,
        default=np.array([])
    )

    output_buffer = NArray(
        label="Output buffer",
        doc="""Array to store temporarily the transformed data.""",
        required=True,
        default=np.array([])
    )

    dot_factor = NArray(
        label="Dot factor",
        doc="""Array to perform the left dot product upon the input buffer.""",
        required=True,
        default=np.array([[1.0]])
    )

    @property
    def _dot_factor(self):
        return self._assert_size("dot_factor", dim=1)

    def configure(self):
        super(DotProduct, self).configure()
        self._dot_factor

    def compute(self):
        """Method that just scales input buffer data to compute the output buffer data."""
        self.output_buffer = np.dot(self._dot_factor * self.input_buffer)


class Integration(Transformer):
    __metaclass__ = ABCMeta

    from tvb.simulator.integrators import Integrator, IntegratorStochastic
    _stochastic_integrator = IntegratorStochastic

    state = NArray(
        label="State",
        doc="""Current state (originally initial condition) of state variable.""",
        required=True,
        default=np.array([[0.0]])
    )

    integrator = Attr(
        field_type=Integrator,
        label="Integration scheme",
        default=CONFIGURED.DEFAULT_INTEGRATOR(dt=CONFIGURED.DEFAULT_DT,
                                              noise=CONFIGURED.DEFAULT_NOISE(
                                                  nsig=np.array([CONFIGURED.DEFAULT_NSIG]))),
        required=True,
        doc="""A tvb.simulator.Integrator object which is
                an integration scheme with supporting attributes such as
                integration step size and noise specification for stochastic
                methods. It is used to compute the time courses of the model state
                variables.""")

    @property
    def _state(self):
        return self._assert_size("state", dim=1)

    @staticmethod
    @abstractmethod
    def dfun(self, X, coupling=0.0, local_coupling=0.0, stimulus=0.0):
        pass

    def compute_next_step(self, input_buffer_element):
        self.state = \
            self.integrator.scheme(self._state, self.dfun,  # X, dfun,
                                   0.0, input_buffer_element, 0.0)  # coupling, local_coupling -> input buffer, stimulus
        self.state = self.apply_boundaries()

    def apply_boundaries(self):
        return self._state

    def transpose(self):
        return self.output_buffer

    def loop_integrate(self, input_buffer):
        output_buffer = []
        for iT in range(input_buffer.shape[1]):
            self.compute_next_step(input_buffer[:, iT])
            output_buffer.append(self._state)
        self.output_buffer = np.array(output_buffer)
        return self.output_buffer

    def configure(self):
        self.integrator.dt = self.dt
        if isinstance(self.integrator, self._stochastic_integrator):
            self.integrator.noise.dt = self.dt
            self.integrator.noise.configure()
        self.integrator.configure()
        super(Integration, self).configure()

    def compute(self, *args, **kwargs):
        """Method for the integration on the input buffer data for the output buffer data ot result."""
        self.loop_integrate(np.array(kwargs.get("input_buffer", self.input_buffer)))
        return self.transpose()


class RatesToSpikes(Scale):
    __metaclass__ = ABCMeta

    """
        RatesToSpikes Transformer abstract base class
    """

    input_buffer = NArray(
        label="Input buffer",
        doc="""Array to store temporarily the data to be transformed.""",
        required=True,
        default=np.array([])
    )

    output_buffer = List(
        of=list,
        doc="""List of spiketrains (lists) storing temporarily the generated spikes.""",
        default=(())
    )

    number_of_neurons = NArray(
        dtype="i",
        label="Number of neurons",
        doc="""Number of neuronal spiketrains to generate for each proxy node.""",
        required=True,
        default=np.array([1]).astype('i')
    )

    def configure(self):
        super(RatesToSpikes, self).configure()
        self._number_of_neurons

    @property
    def _number_of_neurons(self):
        return self._assert_size("number_of_neurons")

    @abstractmethod
    def _compute(self, rates, proxy_count, *args, **kwargs):
        """Abstract method for the computation of rates data transformation to spike trains."""
        pass

    def compute(self, *args, **kwargs):
        """Method for the computation on the input buffer rates' data
           for the output buffer data of spike trains to result."""
        self.output_buffer = []
        for iP, (scale_factor, proxy_buffer) in enumerate(zip(self._scale_factor, self.input_buffer)):
            self.output_buffer.append(self._compute(scale_factor*proxy_buffer, iP, *args, **kwargs))


class SpikesToRates(Scale):
    __metaclass__ = ABCMeta

    """
        RateToSpikes Transformer abstract base class
    """

    input_buffer = List(
        of=list,
        doc="""List of spiketrains (lists) storing temporarily the spikes to be transformed into rates.""",
        default=(())
    )

    output_buffer = NArray(
        label="Output buffer",
        doc="""Array to store temporarily the output rate data.""",
        required=True,
        default=np.array([])
    )

    @abstractmethod
    def _compute(self, spikes, *args, **kwargs):
        """Abstract method for the computation of spike trains data transformation
           to instantaneous mean spiking rates."""
        pass

    @property
    def _scale_factor(self):
        return self._assert_size("scale_factor", "output")

    def configure(self):
        super(SpikesToRates, self).configure()

    def compute(self, *args, **kwargs):
        """Method for the computation on the input buffer spikes' trains' data
           for the output buffer data of instantaneous mean spiking rates to result."""
        output_buffer = []
        for scale_factor, proxy_buffer in zip(self._scale_factor, self.input_buffer):  # At this point we assume that input_buffer has shape (proxy,)
            output_buffer.append(scale_factor * self._compute(proxy_buffer, *args, **kwargs))
        self.output_buffer = np.array(output_buffer)
        return self.output_buffer
