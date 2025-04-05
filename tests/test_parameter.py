import pytest
from ptm import *


def test_map_parameter():
    param = Parameter(
        {
            "iteration": 100,
            "debug": True,
            "name": "ptm",
        }
    )
    assert param.get("iteration") == 100
    assert param.get("debug") is True
    assert param.get("name") == "ptm"
    assert param.get("nonexistent") is None


def test_empty_parameter():
    param = Parameter()
    assert param.get("any_key") is None


def test_pattern_parameter():
    def partial_parameter(current, parent, key):
        match key:
            case "iteration":
                return 100
            case "debug":
                return True
            case "name":
                return "ptm"
    param = Parameter(partial_parameter)
    assert param.get("iteration") == 100
    assert param.get("debug") == True
    assert param.get("name") == "ptm"
    assert param.get("nonexistent") is None

    def programmable_parameter(current, parent, key):
        match key:
            case "slibling_key":
                return 100
            case "iteration_new":
                return parent("iteration") + current("slibling_key")

    param = param + Parameter(programmable_parameter)
    assert param.get("iteration_new") == 200


def test_derived_parameter():
    base_param = Parameter({"key1": "value1", "key2": "value2"})
    derived_param = base_param + Parameter({"key1": "value1_new", "key2": "value2_new"})

    assert derived_param.get("key1") == "value1_new"
    assert derived_param.get("key2") == "value2_new"

    derived_param = derived_param + {"key1": "value1", "key2": "value2"}
    assert derived_param.get("nonexistent") is None
    assert derived_param.get("key1") == "value1"
    assert derived_param.get("key2") == "value2"


def test_invalid_parameter():
    with pytest.raises(TypeError):
        Parameter(123)
