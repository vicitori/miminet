import pytest
from conftest import MiminetTester
from utils.networks import MiminetTestNetwork, NodeType
from selenium.webdriver.common.by import By


class TestEdgeDuplicateForm:
    @pytest.fixture
    def network(self, selenium: MiminetTester):
        net = MiminetTestNetwork(selenium)
        h1 = net.add_node(NodeType.Host, 30, 30)
        h2 = net.add_node(NodeType.Host, 70, 30)
        net.add_edge(h1, h2)
        yield net
        net.delete()

    def test_edge_duplicate_written_from_form(
        self, selenium: MiminetTester, network: MiminetTestNetwork
    ):
        edge = network.edges[0]
        edge_id = 0

        network.open_edge_config(edge)

        selenium.execute_script("$('#edge_duplicate').val(42).trigger('input')")

        selenium.find_element(
            By.CSS_SELECTOR, "#config_edge_main_form_submit_button"
        ).click()

        selenium.wait_for(
            lambda _: network.edges[edge_id]["data"].get("duplicate_percentage") == 42
        )

        assert network.edges[edge_id]["data"].get("duplicate_percentage") == 42

    def test_edge_save_button_updates_json(
        self, selenium: MiminetTester, network: MiminetTestNetwork
    ):
        edge = network.edges[0]
        edge_id = 0

        network.open_edge_config(edge)
        selenium.execute_script("$('#edge_duplicate').val(0).trigger('input')")
        selenium.find_element(
            By.CSS_SELECTOR, "#config_edge_main_form_submit_button"
        ).click()
        selenium.wait_for(
            lambda _: network.edges[edge_id]["data"].get("duplicate_percentage") == 0
        )

        network.open_edge_config(network.edges[edge_id])
        selenium.execute_script("$('#edge_duplicate').val(42).trigger('input')")
        selenium.find_element(
            By.CSS_SELECTOR, "#config_edge_main_form_submit_button"
        ).click()
        selenium.wait_for(
            lambda _: network.edges[edge_id]["data"].get("duplicate_percentage") == 42
        )

        network.open_edge_config(network.edges[edge_id])
        selenium.execute_script("$('#edge_duplicate').val(56).trigger('input')")
        selenium.find_element(
            By.CSS_SELECTOR, "#config_edge_main_form_submit_button"
        ).click()
        selenium.wait_for(
            lambda _: network.edges[edge_id]["data"].get("duplicate_percentage") == 56
        )

        assert network.edges[edge_id]["data"].get("duplicate_percentage") == 56

        network.open_edge_config(network.edges[edge_id])
        field_val = selenium.execute_script(
            "return parseInt($('#edge_duplicate').val()) || 0"
        )
        assert field_val == 56
