from common.utils.flatten_dict import flatten_dict


def test_flatten_simple_dict():
    input_dict = {"a": 1, "b": 2}
    expected = {"a": 1, "b": 2}
    assert flatten_dict(input_dict) == expected


def test_flatten_nested_dict():
    input_dict = {"a": {"b": 1}}
    expected = {"a.b": 1}
    assert flatten_dict(input_dict) == expected


def test_flatten_deeply_nested_dict():
    input_dict = {"a": {"b": {"c": {"d": 5}}}}
    expected = {"a.b.c.d": 5}
    assert flatten_dict(input_dict) == expected


def test_flatten_with_lists():
    input_dict = {"a": [1, 2, {"b": 3}], "c": {"d": ["x", "y"]}}
    expected = {"a.0": 1, "a.1": 2, "a.2.b": 3, "c.d.0": "x", "c.d.1": "y"}
    assert flatten_dict(input_dict) == expected


def test_flatten_mixed():
    input_dict = {"a": {"b": [1, {"c": 2}]}, "d": [True, None]}
    expected = {"a.b.0": 1, "a.b.1.c": 2, "d.0": True, "d.1": None}
    assert flatten_dict(input_dict) == expected


def test_flatten_with_empty_structures():
    input_dict = {"a": [], "b": {}, "c": {"d": {}}}
    expected = {}
    assert flatten_dict(input_dict) == expected


def test_flatten_with_none_and_booleans():
    input_dict = {"a": {"b": None, "c": True}, "d": False}
    expected = {"a.b": None, "a.c": True, "d": False}
    assert flatten_dict(input_dict) == expected


def test_flatten_with_nested_lists_and_dicts():
    input_dict = {"x": [[{"y": 1}], {"z": 2}]}
    expected = {"x.0.0.y": 1, "x.1.z": 2}
    assert flatten_dict(input_dict) == expected


def test_flatten_custom_separator():
    input_dict = {"a": {"b": [1, 2]}}
    expected = {"a->b->0": 1, "a->b->1": 2}
    assert flatten_dict(input_dict, sep="->") == expected
