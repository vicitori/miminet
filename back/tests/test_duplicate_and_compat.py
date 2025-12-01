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


def test_duplicate_packet_counts():
    # duplication_network.json already has 100% duplication
    net_dup = json.loads(load_file("duplication_network.json"))

    # baseline: set duplicates to 0
    net_no_dup = json.loads(json.dumps(net_dup))
    for e in net_no_dup.get("edges", []):
        e.setdefault("data", {})["duplicate_percentage"] = 0

    anim_no_dup_json, _ = run_miminet(json.dumps(net_no_dup))
    anim_dup_json, _ = run_miminet(json.dumps(net_dup))

    count_no_dup = sum(len(g) for g in json.loads(anim_no_dup_json))
    count_dup = sum(len(g) for g in json.loads(anim_dup_json))

    assert count_no_dup > 0
    assert count_dup > count_no_dup
