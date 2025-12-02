import pytest
from selenium.webdriver.common.by import By
from utils.networks import NodeType, MiminetTestNetwork
from utils.locators import Location
from conftest import MiminetTester


class TestDuplicateBasic:
    @pytest.fixture(scope="class")
    def network(self, selenium: MiminetTester):
        network = MiminetTestNetwork(selenium)

        h1 = network.add_node(NodeType.Host)
        h2 = network.add_node(NodeType.Host)
        network.add_edge(h1, h2)

        yield network
        network.delete()

    def test_duplicate_value(
        self, selenium: MiminetTester, network: MiminetTestNetwork
    ):
        edge = network.edges[0]
        network.open_edge_config(edge)

        dup_field = selenium.find_element(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        )

        dup_field.clear()
        dup_field.send_keys("30")

        selenium.find_element(
            By.CSS_SELECTOR,
            Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector,
        ).click()

        selenium.wait_for(
            lambda _: network.edges[0]["data"].get("duplicate_percentage") == "30"
        )

        assert network.edges[0]["data"]["duplicate_percentage"] == "30"


class TestDuplicateEmulation:
    @pytest.fixture(scope="class")
    def network(self, selenium: MiminetTester):
        network = MiminetTestNetwork(selenium)

        h1 = network.add_node(NodeType.Host)
        h2 = network.add_node(NodeType.Host)
        network.add_edge(h1, h2)

        # config host1 → ping host2
        cfg = network.open_node_config(h1)
        cfg.fill_link("10.0.0.1", 24)
        cfg.add_jobs(
            1, {Location.Network.ConfigPanel.Host.Job.PING_FIELD.selector: "10.0.0.2"}
        )
        cfg.submit()

        cfg2 = network.open_node_config(h2)
        cfg2.fill_link("10.0.0.2", 24)
        cfg2.submit()

        yield network
        network.delete()

    def test_duplicate_changes_packet_count(
        self, selenium: MiminetTester, network: MiminetTestNetwork
    ):
        edge = network.edges[0]
        network.open_edge_config(edge)

        # Сначала запускаем эмуляцию, чтобы получить базовое количество пакетов
        packets_before = network.run_emulation()

        dup_elem = selenium.find_element(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        )
        # Очистим поле и установим 100% дублирование
        dup_elem.clear()
        dup_elem.send_keys("100")  # 100% duplication

        selenium.find_element(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector
        ).click()

        # Ждём, пока конфигурация применится в модели сети
        selenium.wait_for(
            lambda _: network.edges[0]["data"].get("duplicate_percentage") == "100"
        )

        packets_after = network.run_emulation()

        # Ожидаем детерминированного увеличения числа пакетов
        assert len(packets_after) > len(packets_before), "Duplicate did not increase packet count"


class TestDuplicateCopyNetwork:
    @pytest.fixture(scope="class")
    def network(self, selenium: MiminetTester):
        network = MiminetTestNetwork(selenium)

        h1 = network.add_node(NodeType.Host)
        h2 = network.add_node(NodeType.Host)

        network.add_edge(h1, h2)

        # set duplicate=50
        edge = network.edges[0]
        network.open_edge_config(edge)
        selenium.find_element(
            By.CSS_SELECTOR, Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        ).send_keys("50")

        selenium.find_element(
            By.CSS_SELECTOR,
            Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector,
        ).click()

        yield network
        network.delete()

    def test_duplicate_preserved_on_copy(
        self, selenium: MiminetTester, network: MiminetTestNetwork
    ):

        selenium.get(network.url)

        initial_edges = network.edges

        selenium.find_element(
            By.CSS_SELECTOR, Location.Network.TopButton.COPY.selector
        ).click()

        selenium.wait_until_appear(By.XPATH, Location.Network.MODAL_DIALOG.xpath)

        selenium.find_element(
            By.XPATH, Location.Network.ModalButton.GO_TO_EDITING.xpath
        ).click()

        copy_net = MiminetTestNetwork(selenium, selenium.current_url)

        assert copy_net.url != network.url

        assert copy_net.edges[0]["data"].get("duplicate_percentage") == initial_edges[
            0
        ]["data"].get("duplicate_percentage")
