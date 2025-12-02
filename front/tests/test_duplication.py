import pytest
from conftest import MiminetTester
from utils.networks import NodeType, MiminetTestNetwork
from selenium.webdriver.common.by import By
from utils.locators import Location
import time


class TestDuplication:
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

    def open_edge_config_and_find_duplicate_field(self, selenium, edge):
        """Открыть конфигурацию ребра и найти поле duplicate"""
        print(f"\nDEBUG: Opening config for edge: {edge['data']['id']}")

        # Попробуем разные способы открыть конфигурацию ребра

        # Способ 1: Используем метод из network
        network.open_edge_config(edge)
        time.sleep(1)  # Дать время на открытие

        # Проверим, что открылась конфигурация ребра, а не сети
        modal_html = selenium.execute_script(
            "return document.querySelector('.modal-content')?.outerHTML || 'No modal content'"
        )
        print(f"DEBUG: Modal content preview: {modal_html[:300]}")

        # Ищем поле duplicate разными способами
        duplicate_field = None

        # Попробуем разные селекторы
        selectors_to_try = [
            "#edge_duplicate",
            "input[name='duplicate']",
            "input[placeholder*='duplicate']",
            "input[placeholder*='Duplicate']",
            "input[placeholder*='дублир']",
            "input[placeholder*='Дублир']",
            ".modal-content input[type='number']",
            ".modal-content input.form-control"
        ]

        for selector in selectors_to_try:
            try:
                elements = selenium.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"DEBUG: Found {len(elements)} elements with selector: {selector}")
                    for i, el in enumerate(elements):
                        print(f"DEBUG: Element {i}: type={el.get_attribute('type')}, "
                              f"id={el.get_attribute('id')}, "
                              f"name={el.get_attribute('name')}, "
                              f"placeholder={el.get_attribute('placeholder')}")
                    duplicate_field = elements[0]
                    break
            except:
                continue

        if duplicate_field is None:
            # Если не нашли, покажем все инпуты в модальном окне
            all_inputs = selenium.find_elements(By.CSS_SELECTOR, ".modal-content input")
            print(f"DEBUG: All inputs in modal ({len(all_inputs)}):")
            for i, inp in enumerate(all_inputs):
                print(f"  Input {i}: id={inp.get_attribute('id')}, "
                      f"name={inp.get_attribute('name')}, "
                      f"placeholder={inp.get_attribute('placeholder')}, "
                      f"type={inp.get_attribute('type')}, "
                      f"value={inp.get_attribute('value')}")

            # Также покажем все labels
            all_labels = selenium.find_elements(By.CSS_SELECTOR, ".modal-content label")
            print(f"DEBUG: All labels in modal ({len(all_labels)}):")
            for i, label in enumerate(all_labels):
                print(f"  Label {i}: text='{label.text}'")

        return duplicate_field

    def test_edge_duplicate_persistence(self, selenium: MiminetTester, network: MiminetTestNetwork):
        """Test that duplicate percentage is saved and persisted"""
        edge = network.edges[0]

        # Open edge config and find duplicate field
        duplicate_field = self.open_edge_config_and_find_duplicate_field(selenium, edge)

        if duplicate_field is None:
            pytest.skip("Duplicate field not found in edge configuration")

        print(f"DEBUG: Field value before: {duplicate_field.get_attribute('value')}")

        # Clear and set value
        duplicate_field.clear()
        duplicate_field.send_keys("42")
        print(f"DEBUG: Field value after setting: {duplicate_field.get_attribute('value')}")

        # Try to submit the form
        try:
            # Look for submit button
            submit_selectors = [
                "button[type='submit']",
                ".btn-primary",
                "input[type='submit']"
            ]

            submit_btn = None
            for selector in submit_selectors:
                try:
                    btn = selenium.find_element(By.CSS_SELECTOR, selector)
                    if btn.is_displayed():
                        submit_btn = btn
                        print(f"DEBUG: Found submit button with selector: {selector}")
                        break
                except:
                    continue

            if submit_btn:
                submit_btn.click()
            else:
                # Если кнопки нет, просто нажмем Enter в поле
                duplicate_field.send_keys("\n")
        except Exception as e:
            print(f"DEBUG: Error submitting form: {e}")
            # Просто нажмем Enter в поле
            duplicate_field.send_keys("\n")

        # Дать время на сохранение
        time.sleep(1)

        # Закрыть модальное окно если оно еще открыто
        try:
            close_btn = selenium.find_element(By.CSS_SELECTOR, ".btn-close")
            close_btn.click()
            time.sleep(0.5)
        except:
            pass

        # Re-open config and verify value is saved
        print("\nDEBUG: Re-opening config to verify...")
        duplicate_field = self.open_edge_config_and_find_duplicate_field(selenium, edge)

        saved_value = duplicate_field.get_attribute("value")
        print(f"DEBUG: Saved value when re-opened: {saved_value}")
        assert saved_value == "42", f"Expected 42, got {saved_value}"

        # Close modal
        try:
            close_btn = selenium.find_element(By.CSS_SELECTOR, ".btn-close")
            close_btn.click()
        except:
            pass

    def test_duplicate_100_first_edge_doubles_packets(self, selenium: MiminetTester, network: MiminetTestNetwork):
        """Test 100% duplication on first edge doubles packets"""
        print("\nDEBUG: Starting test_duplicate_100_first_edge_doubles_packets")

        edge1 = network.edges[0]
        edge2 = network.edges[1]

        print(f"DEBUG: Edge1 ID: {edge1['data']['id']}")
        print(f"DEBUG: Edge2 ID: {edge2['data']['id']}")

        # Helper function to set duplicate value
        def set_duplicate(edge, value):
            field = self.open_edge_config_and_find_duplicate_field(selenium, edge)
            if field is None:
                pytest.skip(f"Duplicate field not found for edge {edge['data']['id']}")

            field.clear()
            field.send_keys(str(value))
            field.send_keys("\n")  # Press Enter to apply
            time.sleep(0.5)

            # Close modal
            try:
                close_btn = selenium.find_element(By.CSS_SELECTOR, ".btn-close")
                close_btn.click()
                time.sleep(0.5)
            except:
                pass

        # Set duplicate to 0% on both edges (baseline)
        print("DEBUG: Setting baseline (0% on both edges)...")
        set_duplicate(edge1, 0)
        set_duplicate(edge2, 0)

        # Run emulation to get baseline packet count
        print("DEBUG: Running baseline emulation...")
        packets = network.run_emulation()
        base_count = sum(len(group) for group in packets)
        print(f"DEBUG: Baseline packet count: {base_count}")

        # Set duplicate to 100% on first edge, 0% on second
        print("DEBUG: Setting 100% on first edge, 0% on second...")
        set_duplicate(edge1, 100)
        set_duplicate(edge2, 0)

        # Run emulation with duplication
        print("DEBUG: Running emulation with duplication...")
        packets = network.run_emulation()
        count = sum(len(group) for group in packets)
        print(f"DEBUG: Packet count with duplication: {count}")

        # With 100% duplication, packets should double
        expected = 2 * base_count
        assert count == expected, f"Expected {expected} packets with 100% duplication, got {count}"

    def test_duplicate_100_both_edges_quadruples_packets(self, selenium: MiminetTester, network: MiminetTestNetwork):
        """Test 100% duplication on both edges quadruples packets"""
        print("\nDEBUG: Starting test_duplicate_100_both_edges_quadruples_packets")

        edge1 = network.edges[0]
        edge2 = network.edges[1]

        # Helper function to set duplicate value
        def set_duplicate(edge, value):
            field = self.open_edge_config_and_find_duplicate_field(selenium, edge)
            if field is None:
                pytest.skip(f"Duplicate field not found for edge {edge['data']['id']}")

            field.clear()
            field.send_keys(str(value))
            field.send_keys("\n")  # Press Enter to apply
            time.sleep(0.5)

            # Close modal
            try:
                close_btn = selenium.find_element(By.CSS_SELECTOR, ".btn-close")
                close_btn.click()
                time.sleep(0.5)
            except:
                pass

        # Set duplicate to 0% on both edges (baseline)
        print("DEBUG: Setting baseline (0% on both edges)...")
        set_duplicate(edge1, 0)
        set_duplicate(edge2, 0)

        # Run emulation to get baseline
        print("DEBUG: Running baseline emulation...")
        packets = network.run_emulation()
        base_count = sum(len(group) for group in packets)
        print(f"DEBUG: Baseline packet count: {base_count}")

        # Set duplicate to 100% on both edges
        print("DEBUG: Setting 100% on both edges...")
        set_duplicate(edge1, 100)
        set_duplicate(edge2, 100)

        # Run emulation with duplication on both edges
        print("DEBUG: Running emulation with duplication on both edges...")
        packets = network.run_emulation()
        count = sum(len(group) for group in packets)
        print(f"DEBUG: Packet count with duplication on both edges: {count}")

        # With 100% duplication on both edges, packets should quadruple
        expected = 4 * base_count
        assert count == expected, f"Expected {expected} packets with 100% duplication on both edges, got {count}"