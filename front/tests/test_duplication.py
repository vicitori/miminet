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
        edge_id = edge["data"]["id"]
        print(f"\nDEBUG: Testing edge ID: {edge_id}")

        network.open_edge_config(edge)

        modal_html = selenium.execute_script(
            "return document.querySelector('.modal-content')?.outerHTML || 'No modal content'"
        )
        print(f"DEBUG: Modal HTML (first 500 chars): {modal_html[:500]}")

        selector = Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        print(f"DEBUG: Using selector: {selector}")

        # ensure we really opened edge config (modal can be network config instead)
        try:
            duplicate_field = selenium.wait_until_appear(By.CSS_SELECTOR, selector, timeout=1)
        except Exception:
            print("DEBUG: Edge form not open, calling ShowEdgeConfig and retrying")
            selenium.execute_script(f"ShowEdgeConfig('{edge_id}')")
            duplicate_field = selenium.wait_until_appear(By.CSS_SELECTOR, selector, timeout=5)

        print(f"DEBUG: duplicate_field found: {duplicate_field}")
        print(f"DEBUG: Field value before: {duplicate_field.get_attribute('value')}")

        duplicate_field.clear()
        duplicate_field.send_keys("42")
        print(
            f"DEBUG: Field value after setting: {duplicate_field.get_attribute('value')}"
        )

        submit_btn = selenium.find_element(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector
        )
        submit_btn.click()

        selenium.wait_until_disappear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.MAIN_FORM.selector
        )

        network.open_edge_config(edge)
        duplicate_field = selenium.wait_until_appear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        )

        saved_value = duplicate_field.get_attribute("value")
        print(f"DEBUG: Saved value when re-opened: {saved_value}")
        assert saved_value == "42", f"Expected 42, got {saved_value}"

        selenium.find_element(
            By.XPATH, Location.Network.ModalButton.GO_TO_EDITING.xpath
        ).click()

    def test_duplicate_100_first_edge_doubles_packets(
        self, selenium: MiminetTester, network: MiminetTestNetwork
    ):
        print("\nDEBUG: Starting test_duplicate_100_first_edge_doubles_packets")

        edge1 = network.edges[0]
        edge2 = network.edges[1]

        print(f"DEBUG: Edge1 ID: {edge1['data']['id']}")
        print(f"DEBUG: Edge2 ID: {edge2['data']['id']}")

        print("DEBUG: Setting baseline (0% on both edges)...")

        network.open_edge_config(edge1)
        duplicate_field = selenium.wait_until_appear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        )
        duplicate_field.clear()
        duplicate_field.send_keys("0")

        submit_btn = selenium.find_element(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector
        )
        submit_btn.click()

        selenium.wait_until_disappear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.MAIN_FORM.selector
        )

        network.open_edge_config(edge2)
        duplicate_field = selenium.wait_until_appear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        )
        duplicate_field.clear()
        duplicate_field.send_keys("0")

        submit_btn = selenium.find_element(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector
        )
        submit_btn.click()

        selenium.wait_until_disappear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.MAIN_FORM.selector
        )

        print("DEBUG: Running baseline emulation...")
        packets = network.run_emulation()
        base_count = sum(len(group) for group in packets)
        print(f"DEBUG: Baseline packet count: {base_count}")

        print("DEBUG: Setting 100% on first edge, 0% on second...")

        network.open_edge_config(edge1)
        duplicate_field = selenium.wait_until_appear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        )
        duplicate_field.clear()
        duplicate_field.send_keys("100")

        submit_btn = selenium.find_element(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector
        )
        submit_btn.click()

        selenium.wait_until_disappear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.MAIN_FORM.selector
        )

        network.open_edge_config(edge2)
        duplicate_field = selenium.wait_until_appear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        )
        duplicate_field.clear()
        duplicate_field.send_keys("0")

        submit_btn = selenium.find_element(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector
        )
        submit_btn.click()

        selenium.wait_until_disappear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.MAIN_FORM.selector
        )

        print("DEBUG: Running emulation with duplication...")
        packets = network.run_emulation()
        count = sum(len(group) for group in packets)
        print(f"DEBUG: Packet count with duplication: {count}")

        expected = 2 * base_count
        assert (
            count == expected
        ), f"Expected {expected} packets with 100% duplication, got {count}"

    def test_duplicate_100_both_edges_quadruples_packets(
        self, selenium: MiminetTester, network: MiminetTestNetwork
    ):
        print("\nDEBUG: Starting test_duplicate_100_both_edges_quadruples_packets")

        edge1 = network.edges[0]
        edge2 = network.edges[1]

        print("DEBUG: Setting baseline (0% on both edges)...")

        network.open_edge_config(edge1)
        duplicate_field = selenium.wait_until_appear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        )
        duplicate_field.clear()
        duplicate_field.send_keys("0")

        submit_btn = selenium.find_element(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector
        )
        submit_btn.click()

        selenium.wait_until_disappear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.MAIN_FORM.selector
        )

        network.open_edge_config(edge2)
        duplicate_field = selenium.wait_until_appear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        )
        duplicate_field.clear()
        duplicate_field.send_keys("0")

        submit_btn = selenium.find_element(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector
        )
        submit_btn.click()

        selenium.wait_until_disappear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.MAIN_FORM.selector
        )

        print("DEBUG: Running baseline emulation...")
        packets = network.run_emulation()
        base_count = sum(len(group) for group in packets)
        print(f"DEBUG: Baseline packet count: {base_count}")

        print("DEBUG: Setting 100% on both edges...")

        network.open_edge_config(edge1)
        duplicate_field = selenium.wait_until_appear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        )
        duplicate_field.clear()
        duplicate_field.send_keys("100")

        submit_btn = selenium.find_element(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector
        )
        submit_btn.click()

        selenium.wait_until_disappear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.MAIN_FORM.selector
        )

        network.open_edge_config(edge2)
        duplicate_field = selenium.wait_until_appear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        )
        duplicate_field.clear()
        duplicate_field.send_keys("100")

        submit_btn = selenium.find_element(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector
        )
        submit_btn.click()

        selenium.wait_until_disappear(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.MAIN_FORM.selector
        )

        print("DEBUG: Running emulation with duplication on both edges...")
        packets = network.run_emulation()
        count = sum(len(group) for group in packets)
        print(f"DEBUG: Packet count with duplication on both edges: {count}")

        expected = 4 * base_count
        assert (
            count == expected
        ), f"Expected {expected} packets with 100% duplication on both edges, got {count}"
