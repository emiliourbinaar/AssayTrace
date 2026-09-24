from assaytrace.artifacts import canonical_json


def test_canonical_json_preserves_types_with_sorted_keys_and_utf8():
    assert canonical_json({"z": 1.0, "a": "µM", "n": None}) == (
        '{"a":"µM","n":null,"z":1.0}\n'.encode("utf-8")
    )


def test_nonfinite_source_floats_are_tagged_instead_of_json_nan():
    assert canonical_json({"value": float("nan")}) == (
        b'{"value":{"source_type":"float","value":"NaN"}}\n'
    )


def test_nonfinite_values_inside_arrays_preserve_sign_and_missingness():
    assert canonical_json([float("inf"), float("-inf"), None, "NaN"]) == (
        b'[{"source_type":"float","value":"Infinity"},'
        b'{"source_type":"float","value":"-Infinity"},null,"NaN"]\n'
    )
