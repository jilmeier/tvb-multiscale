# -*- coding: utf-8 -*-

from tvb_multiscale.tvb_nest.config import CONFIGURED, initialize_logger
from tvb_multiscale.tvb_nest.interfaces.base import TVBNESTInterface

from tvb.simulator.models.reduced_wong_wang_exc_io import ReducedWongWangExcIO
from tvb.simulator.models.reduced_wong_wang_exc_io_inh_i import ReducedWongWangExcIOInhI
from tvb.simulator.models.wilson_cowan_constraint import WilsonCowan as WilsonCowanSimModel
from tvb.simulator.models.generic_2d_oscillator_multiscale import Generic2dOscillator as Generic2dOscillatorSimModel


LOG = initialize_logger(__name__)


class Linear(TVBNESTInterface):
    tvb_model = ReducedWongWangExcIO()

    def __init__(self, config=CONFIGURED):
        super(Linear, self).__init__(config)
        LOG.info("%s created!" % self.__class__)


class RedWWexcIO(TVBNESTInterface):
    tvb_model = ReducedWongWangExcIO()

    def __init__(self, config=CONFIGURED):
        super(RedWWexcIO, self).__init__(config)
        LOG.info("%s created!" % self.__class__)


class RedWWexcIOinhI(TVBNESTInterface):
    tvb_model = ReducedWongWangExcIOInhI()

    def __init__(self, config=CONFIGURED):
        super(RedWWexcIOinhI, self).__init__(config)
        LOG.info("%s created!" % self.__class__)


class Generic2dOscillator(TVBNESTInterface):
    tvb_model = Generic2dOscillatorSimModel()

    def __init__(self, config=CONFIGURED):
        super(Generic2dOscillator, self).__init__(config)
        LOG.info("%s created!" % self.__class__)


class WilsonCowan(TVBNESTInterface):
    tvb_model = WilsonCowanSimModel()

    def __init__(self, config=CONFIGURED):
        super(WilsonCowan, self).__init__(config)
        LOG.info("%s created!" % self.__class__)
