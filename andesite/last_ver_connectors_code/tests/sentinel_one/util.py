import json
import os
from pathlib import Path


def read_json_to_dict(file_path):
    test_directory = Path(os.path.dirname(os.path.abspath(__file__)) + f"/test_data/{file_path}")
    with test_directory.open("r") as file:
        return json.load(file)


def read_json_file_for_resource(resource):
    if "endpoint" in resource:
        json_response = read_json_to_dict("endpoints.json")
    elif "threats" in resource:
        json_response = read_json_to_dict("threats.json")
    elif "alerts" in resource:
        json_response = read_json_to_dict("alerts.json")
    else:
        return None
    assert json_response
    return json_response
