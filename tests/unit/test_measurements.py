from assaytrace.profile import pic50


def test_surrounding_whitespace_does_not_change_an_exact_measurement():
    try:
        result = pic50(" 10 ", " nM ", " = ")
    except ValueError:
        result = None
    assert result == "8.000000000000"
import pytest


def test_pic50_converts_nanomolar_concentration_to_molar_log_scale():
    assert pic50("1", "nM", "=") == "9.000000000000"


def test_pic50_converts_micromolar_units():
    assert pic50("1", "uM", "=") == "6.000000000000"


def test_censored_measurement_is_not_an_exact_label():
    with pytest.raises(ValueError, match="non_exact_relation"):
        pic50("1", "nM", ">")


@pytest.mark.parametrize("unit, expected", [
    ("M", "0.000000000000"), ("mM", "3.000000000000"),
    ("µM", "6.000000000000"), ("μM", "6.000000000000"),
    ("pM", "12.000000000000"), (" nM ", "9.000000000000"),
])
def test_approved_units_are_recognized(unit, expected):
    assert pic50("1", unit, "=") == expected


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity", "0", "-1"])
def test_nonfinite_or_nonpositive_values_have_an_exclusion_reason(value):
    with pytest.raises(ValueError, match="^nonfinite_or_nonpositive_value$"):
        pic50(value, "nM", "=")


@pytest.mark.parametrize("value", [None, "", "unknown"])
def test_missing_or_malformed_values_have_an_exclusion_reason(value):
    with pytest.raises(ValueError, match="^missing_or_invalid_value$"):
        pic50(value, "nM", "=")


@pytest.mark.parametrize("unit", [None, "", "nm", "mg/L"])
def test_unknown_units_have_an_exclusion_reason(unit):
    with pytest.raises(ValueError, match="^unknown_unit$"):
        pic50("1", unit, "=")
