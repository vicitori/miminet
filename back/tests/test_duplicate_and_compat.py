import json
from pathlib import Path

import pytest

from src.tasks import run_miminet

TEST_JSON_DIR = Path("test_json/")


def load_file(name: str) -> str:
    path = TEST_JSON_DIR / name
    return path.read_text()


def test_backward_compatibility_no_dup_percentage():
    net_json = load_file("issues_no_dup_backward_compatibility_network.json")

    animation_json, _ = run_miminet(net_json)
    animation = json.loads(animation_json)

    for packet_group in animation:
        for pkt in packet_group:
            cfg = pkt.get("config", {})
            assert (
                "duplicate_percentage" in cfg
            ), "duplicate_percentage missing in packet config"


def test_backward_compatibility_no_loss_no_dup_percentage():
    net_json = load_file("issues_no_loss_no_dup_backward_compatibility_network.json")

    animation_json, _ = run_miminet(net_json)
    animation = json.loads(animation_json)

    for packet_group in animation:
        for pkt in packet_group:
            cfg = pkt.get("config", {})
            assert "loss_percentage" in cfg, "loss_percentage missing in packet config"
            assert (
                "duplicate_percentage" in cfg
            ), "duplicate_percentage missing in packet config"


@pytest.mark.flaky(reruns=1)
def test_duplicate_increases_packets():
    net = json.loads(load_file("router_network.json"))

    if "edges" not in net or not net["edges"]:
        pytest.skip("No edges in test network")

    # Prepare two variants: no duplicates and with duplicates
    net_no_dup = json.loads(json.dumps(net))
    net_dup = json.loads(json.dumps(net))

    # Set duplicate_percentage for all edges accordingly
    for e in net_no_dup.get("edges", []):
        data = e.setdefault("data", {})
        data["duplicate_percentage"] = 0
        data["loss_percentage"] = data.get("loss_percentage", 0)

    for e in net_dup.get("edges", []):
        data = e.setdefault("data", {})
        data["duplicate_percentage"] = 80
        data["loss_percentage"] = data.get("loss_percentage", 0)

    anim_no_dup_json, _ = run_miminet(json.dumps(net_no_dup))
    anim_dup_json, _ = run_miminet(json.dumps(net_dup))

    anim_no_dup = json.loads(anim_no_dup_json)
    anim_dup = json.loads(anim_dup_json)

    count_no_dup = sum(len(g) for g in anim_no_dup)
    count_dup = sum(len(g) for g in anim_dup)

    assert (
        count_dup > count_no_dup
    ), "Duplicate percentage did not increase number of packets"
