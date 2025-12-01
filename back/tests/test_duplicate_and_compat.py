import json
from pathlib import Path

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
