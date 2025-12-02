import pytest
from conftest import MiminetTester
from utils.networks import NodeType, MiminetTestNetwork
from selenium.webdriver.common.by import By
from utils.locators import Location
import time


class TestDuplicationSimple:
    @pytest.fixture(scope="class")
    def network(self, selenium: MiminetTester):
        network = MiminetTestNetwork(selenium)

        host1_id = network.add_node(NodeType.Host)
        hub_id = network.add_node(NodeType.Hub)
        host2_id = network.add_node(NodeType.Host)

        # edges: host1 - hub - host2
        network.add_edge(host1_id, hub_id)
        network.add_edge(hub_id, host2_id)

        # configure host 1
        config0 = network.open_node_config(host1_id)
        config0.fill_link("192.168.1.1", 24)
        config0.add_jobs(
            1,
            {Location.Network.ConfigPanel.Host.Job.PING_FIELD.selector: "192.168.1.2"},
        )
        config0.submit()

        # configure host 2
        config1 = network.open_node_config(host2_id)
        config1.fill_link("192.168.1.2", 24)
        config1.submit()

        yield network

        network.delete()

    def configure_edge_duplicate(self, selenium, edge_id, duplicate_value):
        """Настроить дублирование для ребра напрямую через JavaScript"""
        print(f"\nDEBUG: Setting duplicate to {duplicate_value} for edge {edge_id}")

        # 1. Открыть конфигурацию ребра
        selenium.execute_script(f"ShowEdgeConfig('{edge_id}')")
        time.sleep(1)

        # 2. Установить значение в поле duplicate
        selenium.execute_script(f"""
            const duplicateField = document.getElementById('edge_duplicate');
            if (duplicateField) {{
                duplicateField.value = '{duplicate_value}';
                // Триггерим события для обновления состояния
                duplicateField.dispatchEvent(new Event('input', {{bubbles: true}}));
                duplicateField.dispatchEvent(new Event('change', {{bubbles: true}}));
                console.log('Set edge_duplicate to', '{duplicate_value}');
            }}
        """)

        # 3. Нажать кнопку сохранения
        selenium.execute_script("""
            const submitBtn = document.getElementById('config_edge_main_form_submit_button');
            if (submitBtn) {
                submitBtn.click();
                console.log('Clicked submit button');
            }
        """)

        time.sleep(1)

        # 4. Закрыть модальное окно
        selenium.execute_script("""
            const closeBtn = document.querySelector('.btn-close');
            if (closeBtn) {
                closeBtn.click();
            }
        """)

        time.sleep(0.5)

    def test_duplicate_simple(self, selenium: MiminetTester, network: MiminetTestNetwork):
        """Простой тест дублирования"""
        edge1_id = network.edges[0]['data']['id']
        edge2_id = network.edges[1]['data']['id']

        # 1. Установить 0% на обоих ребрах
        self.configure_edge_duplicate(selenium, edge1_id, 0)
        self.configure_edge_duplicate(selenium, edge2_id, 0)

        # Базовое количество пакетов
        packets = network.run_emulation()
        base_count = sum(len(group) for group in packets)
        print(f"DEBUG: Baseline: {base_count} packets")

        # 2. Установить 100% на первом ребре
        self.configure_edge_duplicate(selenium, edge1_id, 100)
        self.configure_edge_duplicate(selenium, edge2_id, 0)

        packets = network.run_emulation()
        count = sum(len(group) for group in packets)
        print(f"DEBUG: With 100% on first edge: {count} packets")

        # Проверяем, что пакетов стало в 2 раза больше
        assert count == 2 * base_count, f"Expected {2 * base_count}, got {count}"

        # 3. Установить 100% на обоих ребрах
        self.configure_edge_duplicate(selenium, edge1_id, 100)
        self.configure_edge_duplicate(selenium, edge2_id, 100)

        packets = network.run_emulation()
        count = sum(len(group) for group in packets)
        print(f"DEBUG: With 100% on both edges: {count} packets")

        # Проверяем, что пакетов стало в 4 раза больше
        assert count == 4 * base_count, f"Expected {4 * base_count}, got {count}"
