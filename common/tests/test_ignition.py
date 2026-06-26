from dataclasses import dataclass

from cereal import log

from openpilot.common import ignition


@dataclass
class FakePandaState:
  pandaType: log.PandaState.PandaType = log.PandaState.PandaType.uno
  ignitionLine: bool = False
  ignitionCan: bool = False


UNKNOWN = log.PandaState.PandaType.unknown
KNOWN = log.PandaState.PandaType.uno


class TestIgnitionState:
  def setup_method(self):
    # Reset the process-lifetime latch between tests.
    ignition.ignition_can_seen = False

  def test_empty(self):
    assert ignition.get_ignition_state([]) is False

  def test_only_unknown_pandas(self):
    # unknown pandas must be ignored; with nothing valid, ignition is False.
    assert ignition.get_ignition_state([FakePandaState(pandaType=UNKNOWN, ignitionLine=True)]) is False

  def test_ignition_line_only_pre_latch(self):
    # Before CAN ignition is ever seen, ignitionLine is trusted.
    states = [FakePandaState(pandaType=KNOWN, ignitionLine=True)]
    assert ignition.get_ignition_state(states) is True

  def test_no_ignition(self):
    states = [FakePandaState(pandaType=KNOWN, ignitionLine=False, ignitionCan=False)]
    assert ignition.get_ignition_state(states) is False

  def test_ignition_can_returns_true_and_latches(self):
    states = [FakePandaState(pandaType=KNOWN, ignitionCan=True)]
    assert ignition.get_ignition_state(states) is True
    assert ignition.ignition_can_seen is True

  def test_post_latch_ignores_ignition_line(self):
    # Mazda symptom: ignitionLine stays high after shutdown. Once CAN ignition
    # has been seen, ignitionLine alone must not count as ignited.
    ignition.ignition_can_seen = True
    states = [FakePandaState(pandaType=KNOWN, ignitionLine=True, ignitionCan=False)]
    assert ignition.get_ignition_state(states) is False

  def test_post_latch_reignites_on_can(self):
    ignition.ignition_can_seen = True
    states = [FakePandaState(pandaType=KNOWN, ignitionCan=True)]
    assert ignition.get_ignition_state(states) is True

  def test_latch_does_not_set_without_can(self):
    # ignitionLine alone must not arm the latch.
    states = [FakePandaState(pandaType=KNOWN, ignitionLine=True)]
    ignition.get_ignition_state(states)
    assert ignition.ignition_can_seen is False

  def test_mixed_pandas(self):
    # A valid panda reporting CAN ignition wins even with unknown pandas present.
    states = [
      FakePandaState(pandaType=UNKNOWN, ignitionLine=True),
      FakePandaState(pandaType=KNOWN, ignitionCan=True),
    ]
    assert ignition.get_ignition_state(states) is True
