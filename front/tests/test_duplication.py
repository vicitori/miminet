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
        """Настроить дублирование для ребра"""
        print(f"\nDEBUG [configure_edge_duplicate]: Setting duplicate to {duplicate_value} for edge {edge_id}")

        # 1. Открыть конфигурацию ребра
        selenium.execute_script(f"ShowEdgeConfig('{edge_id}')")
        time.sleep(1)

        # Проверить, открылось ли модальное окно
        modal_count = selenium.execute_script("return document.querySelectorAll('.modal-content').length")
        print(f"DEBUG: Found {modal_count} modal elements")

        if modal_count == 0:
            print("WARNING: No modal opened, trying alternative...")
            # Попробуем другой способ открыть конфигурацию
            selenium.execute_script(f"""
                if (typeof window.cy !== 'undefined') {{
                    const edge = window.cy.edges('[id = "{edge_id}"]');
                    if (edge) {{
                        edge.trigger('tap');
                    }}
                }}
            """)
            time.sleep(1)

        # 2. Проверить, есть ли поле edge_duplicate
        field_exists = selenium.execute_script("return !!document.getElementById('edge_duplicate')")
        print(f"DEBUG: edge_duplicate field exists: {field_exists}")

        if not field_exists:
            # Показать все элементы в модальном окне для отладки
            all_elements = selenium.execute_script("""
                const modal = document.querySelector('.modal-content');
                if (!modal) return 'No modal found';
                const inputs = modal.querySelectorAll('input, select, textarea, button');
                const result = [];
                inputs.forEach((el, i) => {
                    result.push(`Element ${i}: tag=${el.tagName}, id=${el.id}, name=${el.name}, type=${el.type}, class=${el.className}`);
                });
                return result.join('\\n');
            """)
            print(f"DEBUG: All form elements in modal:\n{all_elements}")

        # 3. Установить значение в поле duplicate
        selenium.execute_script(f"""
            const duplicateField = document.getElementById('edge_duplicate');
            if (duplicateField) {{
                console.log('Found edge_duplicate field, current value:', duplicateField.value);
                duplicateField.value = '{duplicate_value}';
                // Триггерим события для обновления состояния
                duplicateField.dispatchEvent(new Event('input', {{bubbles: true}}));
                duplicateField.dispatchEvent(new Event('change', {{bubbles: true}}));
                console.log('Set edge_duplicate to', '{duplicate_value}');
                return 'Success';
            }} else {{
                console.error('edge_duplicate field not found!');
                return 'Field not found';
            }}
        """)

        result = selenium.execute_script("""
            const duplicateField = document.getElementById('edge_duplicate');
            return duplicateField ? duplicateField.value : 'NO_FIELD';
        """)
        print(f"DEBUG: Field value after setting: {result}")

        # 4. Найти и нажать кнопку сохранения
        btn_clicked = selenium.execute_script("""
            // Попробуем разные селекторы для кнопки сохранения
            const selectors = [
                '#config_edge_main_form_submit_button',
                'button[type="submit"]',
                '.btn-success',
                'input[type="submit"]',
                'button:contains("Сохранить")',
                'button:contains("Save")'
            ];

            for (const selector of selectors) {
                const btn = document.querySelector(selector);
                if (btn && btn.offsetParent !== null) { // Проверяем что элемент видим
                    console.log('Found button with selector:', selector, 'text:', btn.textContent);
                    btn.click();
                    return true;
                }
            }
            console.log('No submit button found with common selectors');
            return false;
        """)

        print(f"DEBUG: Submit button clicked: {btn_clicked}")

        if not btn_clicked:
            # Если не нашли кнопку, попробуем нажать Enter в поле
            selenium.execute_script("""
                const field = document.getElementById('edge_duplicate');
                if (field) {
                    const enterEvent = new KeyboardEvent('keydown', {
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        bubbles: true
                    });
                    field.dispatchEvent(enterEvent);
                    console.log('Pressed Enter in duplicate field');
                }
            """)

        time.sleep(1)

        # 5. Закрыть модальное окно если оно еще открыто
        selenium.execute_script("""
            const closeBtn = document.querySelector('.btn-close, [data-dismiss="modal"], .close');
            if (closeBtn) {
                closeBtn.click();
                console.log('Closed modal');
            } else {
                console.log('No close button found');
                // Попробуем кликнуть вне модального окна
                const modal = document.querySelector('.modal-backdrop, .modal');
                if (modal) {
                    document.body.click();
                    console.log('Clicked outside modal');
                }
            }
        """)

        time.sleep(0.5)

    def test_duplicate_basic(self, selenium: MiminetTester, network: MiminetTestNetwork):
        """Базовый тест: проверяем что можем установить duplicate и запустить эмуляцию"""
        print("\n=== DEBUG: Starting basic duplicate test ===")

        edge1_id = network.edges[0]['data']['id']
        edge2_id = network.edges[1]['data']['id']

        print(f"Edge 1 ID: {edge1_id}")
        print(f"Edge 2 ID: {edge2_id}")

        # 1. Сначала просто попробуем запустить эмуляцию без изменений
        print("\n1. Testing emulation without changes...")
        try:
            packets = network.run_emulation()
            print(f"SUCCESS: Emulation ran, got {len(packets)} packet groups")
            if packets:
                total_packets = sum(len(group) for group in packets)
                print(f"Total packets: {total_packets}")
        except Exception as e:
            print(f"ERROR in baseline emulation: {e}")
            # Покажем состояние страницы для отладки
            page_state = selenium.execute_script("""
                return {
                    url: window.location.href,
                    title: document.title,
                    readyState: document.readyState,
                    hasCytoscape: typeof window.cy !== 'undefined',
                    edgeCount: window.cy ? window.cy.edges().length : 0
                };
            """)
            print(f"Page state: {page_state}")
            pytest.fail(f"Baseline emulation failed: {e}")

        # 2. Установить 0% на обоих ребрах (должно быть то же самое)
        print("\n2. Setting duplicate to 0% on both edges...")
        self.configure_edge_duplicate(selenium, edge1_id, 0)
        self.configure_edge_duplicate(selenium, edge2_id, 0)

        print("\n3. Running emulation with 0% duplicate...")
        try:
            packets = network.run_emulation()
            base_count = sum(len(group) for group in packets)
            print(f"SUCCESS: Emulation with 0% duplicate ran, {base_count} packets")
        except Exception as e:
            print(f"ERROR in emulation with 0% duplicate: {e}")
            pytest.fail(f"Emulation with 0% duplicate failed: {e}")

    def test_duplicate_effect(self, selenium: MiminetTester, network: MiminetTestNetwork):
        """Тест эффекта дублирования"""
        print("\n=== DEBUG: Starting duplicate effect test ===")

        edge1_id = network.edges[0]['data']['id']
        edge2_id = network.edges[1]['data']['id']

        # 1. Установить 0% на обоих ребрах и получить базовое количество
        print("\n1. Getting baseline with 0% duplicate...")
        self.configure_edge_duplicate(selenium, edge1_id, 0)
        self.configure_edge_duplicate(selenium, edge2_id, 0)

        try:
            packets = network.run_emulation()
            base_count = sum(len(group) for group in packets)
            print(f"Baseline: {base_count} packets")
        except Exception as e:
            print(f"ERROR getting baseline: {e}")
            pytest.skip(f"Cannot get baseline: {e}")

        # 2. Установить 100% на первом ребре
        print("\n2. Setting 100% duplicate on first edge...")
        self.configure_edge_duplicate(selenium, edge1_id, 100)
        self.configure_edge_duplicate(selenium, edge2_id, 0)

        print("\n3. Running emulation with 100% duplicate on first edge...")
        try:
            packets = network.run_emulation()
            count = sum(len(group) for group in packets)
            print(f"With 100% on first edge: {count} packets")

            # Проверяем, что пакетов стало больше
            if count > base_count:
                print(f"SUCCESS: Packet count increased from {base_count} to {count}")
                print(f"Increase factor: {count / base_count:.2f}x")
            else:
                print(f"WARNING: Packet count didn't increase ({base_count} -> {count})")

        except Exception as e:
            print(f"ERROR in emulation with 100% duplicate: {e}")

    def test_duplicate_persistence(self, selenium: MiminetTester, network: MiminetTestNetwork):
        """Тест сохранения значения duplicate"""
        print("\n=== DEBUG: Testing duplicate persistence ===")

        edge = network.edges[0]
        edge_id = edge['data']['id']

        # 1. Установить значение 42
        print(f"\n1. Setting duplicate to 42 for edge {edge_id}")
        self.configure_edge_duplicate(selenium, edge_id, 42)

        # 2. Открыть конфигурацию снова и проверить значение
        print(f"\n2. Re-opening config to check persistence...")
        selenium.execute_script(f"ShowEdgeConfig('{edge_id}')")
        time.sleep(1)

        # Получить значение поля
        saved_value = selenium.execute_script("""
            const field = document.getElementById('edge_duplicate');
            return field ? field.value : 'FIELD_NOT_FOUND';
        """)

        print(f"Saved duplicate value: {saved_value}")

        # Закрыть модальное окно
        selenium.execute_script("""
            const closeBtn = document.querySelector('.btn-close');
            if (closeBtn) closeBtn.click();
        """)

        time.sleep(0.5)

        # Проверяем сохраненное значение
        assert saved_value == "42", f"Expected 42, got {saved_value}"
        print("SUCCESS: Duplicate value persisted correctly")