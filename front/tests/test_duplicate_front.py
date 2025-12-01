import pytest
from conftest import MiminetTester
from utils.networks import NodeType, MiminetTestNetwork
from selenium.webdriver.common.by import By
from utils.locators import Location


class TestDuplicateFront:
    @pytest.fixture(scope="function")
    def network(self, selenium: MiminetTester):
        network = MiminetTestNetwork(selenium)

        host1_id = network.add_node(NodeType.Host, x=30, y=50)
        hub_id = network.add_node(NodeType.Hub, x=50, y=50)
        host2_id = network.add_node(NodeType.Host, x=70, y=50)

        network.add_edge(host1_id, hub_id)
        network.add_edge(hub_id, host2_id)

        cfg1 = network.open_node_config(host1_id)
        cfg1.fill_link("192.168.1.1", 24)
        cfg1.add_jobs(
            1,
            {Location.Network.ConfigPanel.Host.Job.PING_FIELD.selector: "192.168.1.2"},
        )
        cfg1.submit()

        cfg2 = network.open_node_config(host2_id)
        cfg2.fill_link("192.168.1.2", 24)
        cfg2.submit()

        yield network

        network.delete()

    def test_duplicate_doubles_packets(
        self, selenium: MiminetTester, network: MiminetTestNetwork
    ):
        # Baseline: both edges duplicate = 0
        for edge in network.edges:
            selenium.execute_script(f"ShowEdgeConfig('{edge['data']['id']}')")
            el = selenium.wait_until_appear(By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector)
            el.clear()
            el.send_keys("0")
            selenium.find_element(By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector).click()

        packets_no_dup = network.run_emulation()
        count_no_dup = sum(len(group) for group in packets_no_dup)

        # Case A: duplicate on first edge only
        # Set edge1 = 100, edge2 = 0
        edge1_id = network.edges[0]["data"]["id"]
        edge2_id = network.edges[1]["data"]["id"]

        selenium.execute_script(f"ShowEdgeConfig('{edge1_id}')")
        el = selenium.wait_until_appear(By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector)
        el.clear(); el.send_keys("100")
        selenium.find_element(By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector).click()

        selenium.execute_script(f"ShowEdgeConfig('{edge2_id}')")
        el = selenium.wait_until_appear(By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector)
        el.clear(); el.send_keys("0")
        selenium.find_element(By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector).click()

        packets_first_dup = network.run_emulation()
        count_first_dup = sum(len(group) for group in packets_first_dup)

        # Expect doubling after first edge
        assert (
            count_first_dup == 2 * count_no_dup
        ), f"Expected packets with duplication on first edge ({count_first_dup}) to be exactly twice packets without duplication ({count_no_dup})"

        # Case B: duplicate on second edge only
        selenium.execute_script(f"ShowEdgeConfig('{edge1_id}')")
        el = selenium.wait_until_appear(By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector)
        el.clear(); el.send_keys("0")
        selenium.find_element(By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector).click()

        selenium.execute_script(f"ShowEdgeConfig('{edge2_id}')")
        el = selenium.wait_until_appear(By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector)
        el.clear(); el.send_keys("100")
        selenium.find_element(By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector).click()

        packets_second_dup = network.run_emulation()
        count_second_dup = sum(len(group) for group in packets_second_dup)

        # Expect doubling after second edge
        assert (
            count_second_dup == 2 * count_no_dup
        ), f"Expected packets with duplication on second edge ({count_second_dup}) to be exactly twice packets without duplication ({count_no_dup})"

        # Case C: duplicate on both edges
        selenium.execute_script(f"ShowEdgeConfig('{edge1_id}')")
        el = selenium.wait_until_appear(By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector)
        el.clear(); el.send_keys("100")
        selenium.find_element(By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector).click()

        selenium.execute_script(f"ShowEdgeConfig('{edge2_id}')")
        el = selenium.wait_until_appear(By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector)
        el.clear(); el.send_keys("100")
        selenium.find_element(By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector).click()

        packets_both_dup = network.run_emulation()
        count_both_dup = sum(len(group) for group in packets_both_dup)

        # Expect doubling on both edges -> 4x
        assert (
            count_both_dup == 4 * count_no_dup
        ), f"Expected packets with duplication on both edges ({count_both_dup}) to be exactly 4x packets without duplication ({count_no_dup})"
