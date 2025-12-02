import pytest
from conftest import MiminetTester
from utils.networks import NodeType, MiminetTestNetwork
from selenium.webdriver.common.by import By
from utils.locators import Location


class TestDuplication:
    @pytest.fixture(scope="class")
    def network(self, selenium: MiminetTester):
        network = MiminetTestNetwork(selenium)

        host1_id = network.add_node(NodeType.Host)
        hub_id = network.add_node(NodeType.Hub)
        host2_id = network.add_node(NodeType.Host)

        network.add_edge(host1_id, hub_id)
        network.add_edge(hub_id, host2_id)

        config0 = network.open_node_config(host1_id)
        config0.fill_link("192.168.1.1", 24)
        config0.add_jobs(
            1,
            {Location.Network.ConfigPanel.Host.Job.PING_FIELD.selector: "192.168.1.2"},
        )
        config0.submit()

        config1 = network.open_node_config(host2_id)
        config1.fill_link("192.168.1.2", 24)
        config1.submit()

        yield network

        network.delete()

    def test_edge_duplicate_persistence(
        self, selenium: MiminetTester, network: MiminetTestNetwork
    ):
        edge = network.edges[0]

        network.open_edge_config(edge)
        duplicate_field = selenium.wait_until_appear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        )

        duplicate_field.clear()
        duplicate_field.send_keys("42")

        selenium.find_element(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector
        ).click()

        selenium.wait_until_disappear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.MAIN_FORM.selector
        )

        network.open_edge_config(edge)
        duplicate_field = selenium.wait_until_appear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        )

        saved_value = duplicate_field.get_attribute("value")
        assert saved_value == "42", f"Expected 42, got {saved_value}"

        selenium.find_element(
            By.XPATH, Location.Network.ModalButton.GO_TO_EDITING.xpath
        ).click()

    def test_duplicate_100_first_edge_doubles_packets(
        self, selenium: MiminetTester, network: MiminetTestNetwork
    ):
        edge1 = network.edges[0]
        edge2 = network.edges[1]

        # Set duplicate to 0% on both edges (baseline)
        network.open_edge_config(edge1)
        duplicate_field = selenium.wait_until_appear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        )
        duplicate_field.clear()
        duplicate_field.send_keys("0")
        selenium.find_element(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector
        ).click()
        selenium.wait_until_disappear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.MAIN_FORM.selector
        )

        network.open_edge_config(edge2)
        duplicate_field = selenium.wait_until_appear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        )
        duplicate_field.clear()
        duplicate_field.send_keys("0")
        selenium.find_element(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector
        ).click()
        selenium.wait_until_disappear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.MAIN_FORM.selector
        )

        packets = network.run_emulation()
        base_count = sum(len(group) for group in packets)

        network.open_edge_config(edge1)
        duplicate_field = selenium.wait_until_appear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        )
        duplicate_field.clear()
        duplicate_field.send_keys("100")
        selenium.find_element(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector
        ).click()
        selenium.wait_until_disappear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.MAIN_FORM.selector
        )

        network.open_edge_config(edge2)
        duplicate_field = selenium.wait_until_appear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        )
        duplicate_field.clear()
        duplicate_field.send_keys("0")
        selenium.find_element(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector
        ).click()
        selenium.wait_until_disappear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.MAIN_FORM.selector
        )

        packets = network.run_emulation()
        count = sum(len(group) for group in packets)

        assert (
            count == 2 * base_count
        ), f"Expected {2 * base_count} packets with 100% duplication, got {count}"

    def test_duplicate_100_both_edges_quadruples_packets(
        self, selenium: MiminetTester, network: MiminetTestNetwork
    ):
        edge1 = network.edges[0]
        edge2 = network.edges[1]

        network.open_edge_config(edge1)
        duplicate_field = selenium.wait_until_appear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        )
        duplicate_field.clear()
        duplicate_field.send_keys("0")
        selenium.find_element(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector
        ).click()
        selenium.wait_until_disappear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.MAIN_FORM.selector
        )

        network.open_edge_config(edge2)
        duplicate_field = selenium.wait_until_appear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        )
        duplicate_field.clear()
        duplicate_field.send_keys("0")
        selenium.find_element(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector
        ).click()
        selenium.wait_until_disappear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.MAIN_FORM.selector
        )

        packets = network.run_emulation()
        base_count = sum(len(group) for group in packets)

        network.open_edge_config(edge1)
        duplicate_field = selenium.wait_until_appear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        )
        duplicate_field.clear()
        duplicate_field.send_keys("100")
        selenium.find_element(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector
        ).click()
        selenium.wait_until_disappear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.MAIN_FORM.selector
        )

        network.open_edge_config(edge2)
        duplicate_field = selenium.wait_until_appear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        )
        duplicate_field.clear()
        duplicate_field.send_keys("100")
        selenium.find_element(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector
        ).click()
        selenium.wait_until_disappear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.MAIN_FORM.selector
        )

        packets = network.run_emulation()
        count = sum(len(group) for group in packets)

        assert (
            count == 4 * base_count
        ), f"Expected {4 * base_count} packets with 100% duplication on both edges, got {count}"
