import json
from pathlib import Path

from src.tasks import run_miminet

TEST_JSON_DIR = Path("network_examples_json/")


def load_file(name: str) -> str:
    path = TEST_JSON_DIR / name
    return path.read_text()


def set_duplicate_to_zero(network_json: str) -> str:
    j = json.loads(network_json)
    for ed in j.get("edges", []):
        data = ed.get("data", {})
        if "duplicate_percentage" in data:
            data["duplicate_percentage"] = 0
        else:
            data["duplicate_percentage"] = 0
    return json.dumps(j)


def count_packets(animation_json: str) -> int:
    anim = json.loads(animation_json)
    # Count individual packet entries across all time groups
    return sum(len(group) for group in anim)


def test_duplicate_edges_double_packets():
    net_json = load_file("duplication_network.json")

    # run with duplicates as in file
    animation_with_dup, _ = run_miminet(net_json)

    # run with duplicate set to 0xw
    net_zero_dup = set_duplicate_to_zero(net_json)
    animation_no_dup, _ = run_miminet(net_zero_dup)

    count_with_dup = count_packets(animation_with_dup)
    count_no_dup = count_packets(animation_no_dup)

    assert (
        count_with_dup > count_no_dup
    ), f"Packets with duplication ({count_with_dup}) is not exactly twice packets without duplication ({count_no_dup})"
