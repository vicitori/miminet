import pytest
from conftest import MiminetTester, selenium
from utils.networks import NodeType, MiminetTestNetwork
from selenium.webdriver.common.by import By
from utils.locators import Location


class TestDuplicationCombined:
    @pytest.fixture(scope="function")
    def network(self, selenium: MiminetTester):
        network = MiminetTestNetwork(selenium)

        h1 = network.add_node(NodeType.Host, x=30, y=50)
        hub = network.add_node(NodeType.Hub, x=50, y=50)
        h2 = network.add_node(NodeType.Host, x=70, y=50)

        network.add_edge(h1, hub)
        network.add_edge(hub, h2)

        cfg1 = network.open_node_config(h1)
        cfg1.fill_link("192.168.1.1", 24)
        cfg1.add_jobs(
            1,
            {Location.Network.ConfigPanel.Host.Job.PING_FIELD.selector: "192.168.1.2"},
        )
        cfg1.submit()

        cfg2 = network.open_node_config(h2)
        cfg2.fill_link("192.168.1.2", 24)
        cfg2.submit()

        yield network

        network.delete()

    def _set_duplicate_js(self, selenium, el, value):
        # set value and dispatch events to trigger app listeners
        selenium.execute_script(
            "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input',{bubbles:true})); arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
            el,
            str(value),
        )
        btn = selenium.find_element(By.XPATH, Location.Network.ModalButton.GO_TO_EDITING.xpath)
        selenium.execute_script("arguments[0].click();", btn)

    def _wait_duplicate_numeric(self, selenium, edge_id, expected, timeout=10):
        selenium.wait_for(lambda d: d.execute_script(
            "const e=(window.edges||[]).find(x=>x.data.id==arguments[0]); return e && (parseInt(e.data.duplicate_percentage)||0) == arguments[1];",
            edge_id,
            int(expected),
        ), timeout=timeout)

    def test_edge_duplicate_written_and_saved(self, selenium: MiminetTester, network: MiminetTestNetwork):
        edge = network.edges[0]
        edge_id = 0

        network.open_edge_config(edge)
        selector = Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        selenium.wait_until_appear(By.CSS_SELECTOR, selector)
        el = selenium.find_element(By.CSS_SELECTOR, selector)

        # set 42 via JS and apply
        self._set_duplicate_js(selenium, el, 42)

        edges_after_submit = selenium.execute_script("return window.edges || null")
        print('\nDEBUG: edges after submit (raw):', edges_after_submit)

        # wait until JS edges array is updated for this edge (numeric compare)
        edge_data_id = edge['data']['id']
        self._wait_duplicate_numeric(selenium, edge_data_id, 42, timeout=10)

        # set 0 then 56 to ensure persistence
        network.open_edge_config(network.edges[edge_id])
        el = selenium.wait_until_appear(By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector)
        self._set_duplicate_js(selenium, el, 0)
        selenium.wait_for(lambda _: network.edges[edge_id]["data"].get("duplicate_percentage") == 0)

        network.open_edge_config(network.edges[edge_id])
        el = selenium.wait_until_appear(By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector)
        self._set_duplicate_js(selenium, el, 56)
        self._wait_duplicate_numeric(selenium, network.edges[edge_id]["data"]["id"], 56, timeout=5)

        assert int(network.edges[edge_id]["data"].get("duplicate_percentage") or 0) == 56

        network.open_edge_config(network.edges[edge_id])
        field_val = int(selenium.execute_script(f"return parseInt(document.querySelector('{Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector}').value) || 0"))
        assert field_val == 56

    def test_duplicate_doubles_packets(self, selenium: MiminetTester, network: MiminetTestNetwork):
        # set duplicate = 0 for all edges initially (use JS set to ensure listeners run)
        for edge in network.edges:
            selenium.execute_script(f"ShowEdgeConfig('{edge['data']['id']}')")
            selector = Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
            selenium.wait_until_appear(By.CSS_SELECTOR, selector)
            el = selenium.find_element(By.CSS_SELECTOR, selector)
            self._set_duplicate_js(selenium, el, 0)

        # debug: show edges state before emulation
        edges_before_emulation = selenium.execute_script("return window.edges || null")
        print('\nDEBUG: edges before emulation (raw):', edges_before_emulation)

        # ensure edge config modal closed before emulation
        try:
            selenium.wait_until_disappear(By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.MAIN_FORM.selector, timeout=5)
        except Exception:
            pass

        packets_no_dup = network.run_emulation()
        # total packets (sum of groups) for baseline
        count_no_dup = sum(len(group) for group in packets_no_dup)

        edge1_id = network.edges[0]["data"]["id"]
        edge2_id = network.edges[1]["data"]["id"]

        # Case A: duplicate on first edge only
        selenium.execute_script(f"ShowEdgeConfig('{edge1_id}')")
        el = selenium.wait_until_appear(By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector)
        self._set_duplicate_js(selenium, el, 100)

        selenium.execute_script(f"ShowEdgeConfig('{edge2_id}')")
        el = selenium.wait_until_appear(By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector)
        self._set_duplicate_js(selenium, el, 0)

        packets_first_dup = network.run_emulation()
        count_first_dup = sum(len(group) for group in packets_first_dup)
        assert count_first_dup == 2 * count_no_dup, f"Expected doubling for first edge: {count_first_dup} vs {count_no_dup}"

        # Case B: duplicate on second edge only
        selenium.execute_script(f"ShowEdgeConfig('{edge1_id}')")
        el = selenium.wait_until_appear(By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector)
        self._set_duplicate_js(selenium, el, 0)

        selenium.execute_script(f"ShowEdgeConfig('{edge2_id}')")
        el = selenium.wait_until_appear(By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector)
        self._set_duplicate_js(selenium, el, 100)

        packets_second_dup = network.run_emulation()
        count_second_dup = sum(len(group) for group in packets_second_dup)
        assert count_second_dup == 2 * count_no_dup, f"Expected doubling for second edge: {count_second_dup} vs {count_no_dup}"

        # Case C: duplicate on both edges
        selenium.execute_script(f"ShowEdgeConfig('{edge1_id}')")
        el = selenium.wait_until_appear(By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector)
        self._set_duplicate_js(selenium, el, 100)

        selenium.execute_script(f"ShowEdgeConfig('{edge2_id}')")
        el = selenium.wait_until_appear(By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector)
        self._set_duplicate_js(selenium, el, 100)

        packets_both_dup = network.run_emulation()
        count_both_dup = sum(len(group) for group in packets_both_dup)
        assert count_both_dup == 4 * count_no_dup, f"Expected 4x when both edges duplicate: {count_both_dup} vs {count_no_dup}"
