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

    def test_edge_config_opens(self, selenium: MiminetTester, network: MiminetTestNetwork):
        """Проверка, что конфигурация ребра вообще открывается"""
        print("\n=== DEBUG: Testing if edge config opens ===")

        edge = network.edges[0]
        edge_id = edge['data']['id']
        print(f"Edge ID: {edge_id}")

        # Способ 1: Попробуем через JavaScript напрямую
        print("\nTrying JavaScript ShowEdgeConfig...")
        try:
            selenium.execute_script(f"ShowEdgeConfig('{edge_id}')")
            time.sleep(2)

            # Проверим, есть ли модальное окно
            modal = selenium.find_elements(By.CSS_SELECTOR, ".modal-content")
            print(f"Found {len(modal)} modal elements")

            if modal:
                modal_html = modal[0].get_attribute('outerHTML')
                print(f"Modal HTML (first 1000 chars):\n{modal_html[:1000]}")

                # Посмотрим все элементы в модальном окне
                all_elements = modal[0].find_elements(By.CSS_SELECTOR, "*")
                print(f"\nTotal elements in modal: {len(all_elements)}")

                # Посмотрим заголовок модального окна
                try:
                    title = modal[0].find_element(By.CSS_SELECTOR, ".modal-title")
                    print(f"Modal title: {title.text}")
                except:
                    print("No modal title found")
            else:
                print("No modal found after ShowEdgeConfig")

        except Exception as e:
            print(f"Error with ShowEdgeConfig: {e}")

        # Способ 2: Попробуем кликнуть по ребру
        print("\nTrying to click on edge...")
        try:
            # Найти элемент ребра на canvas/графе
            edge_element = selenium.find_element(By.CSS_SELECTOR, f"[data-id='{edge_id}']")
            selenium.execute_script("arguments[0].click();", edge_element)
            time.sleep(2)

            # Проверить контекстное меню или модальное окно
            modals = selenium.find_elements(By.CSS_SELECTOR, ".modal, .context-menu")
            print(f"Found {len(modals)} modals/context menus after click")

        except Exception as e:
            print(f"Error clicking edge: {e}")

        # Способ 3: Посмотрим, что есть на странице
        print("\n=== Page analysis ===")
        print("Looking for edge configuration elements...")

        # Ищем любые элементы связанные с ребрами
        all_edge_elements = selenium.find_elements(By.CSS_SELECTOR, "[id*='edge_'], [class*='edge']")
        print(f"Found {len(all_edge_elements)} elements with 'edge' in id or class")

        for i, elem in enumerate(all_edge_elements[:10]):  # первые 10
            elem_id = elem.get_attribute('id') or ''
            elem_class = elem.get_attribute('class') or ''
            print(f"Element {i}: id='{elem_id[:50]}', class='{elem_class[:50]}'")

    def test_find_duplicate_field(self, selenium: MiminetTester, network: MiminetTestNetwork):
        """Поиск поля duplicate на странице"""
        print("\n=== DEBUG: Searching for duplicate field ===")

        # Сначала откроем любую конфигурацию чтобы увидеть структуру
        edge = network.edges[0]
        edge_id = edge['data']['id']

        print(f"1. Checking if ShowEdgeConfig function exists...")
        show_edge_exists = selenium.execute_script("return typeof ShowEdgeConfig === 'function'")
        print(f"   ShowEdgeConfig exists: {show_edge_exists}")

        if show_edge_exists:
            print(f"2. Calling ShowEdgeConfig('{edge_id}')...")
            selenium.execute_script(f"ShowEdgeConfig('{edge_id}')")
            time.sleep(2)

        print("3. Searching for input fields on entire page...")

        # Ищем все input поля на странице
        all_inputs = selenium.find_elements(By.CSS_SELECTOR, "input")
        print(f"   Total inputs on page: {len(all_inputs)}")

        duplicate_candidates = []

        for i, inp in enumerate(all_inputs):
            inp_id = inp.get_attribute('id') or ''
            inp_name = inp.get_attribute('name') or ''
            inp_placeholder = inp.get_attribute('placeholder') or ''
            inp_type = inp.get_attribute('type') or ''
            inp_value = inp.get_attribute('value') or ''

            # Ищем поля, которые могут быть связаны с duplicate
            keywords = ['duplicate', 'дублир', 'процент', 'percentage', 'loss', 'потер']

            for keyword in keywords:
                if (keyword in inp_id.lower() or
                        keyword in inp_name.lower() or
                        keyword in inp_placeholder.lower()):
                    print(f"\n   FOUND POSSIBLE DUPLICATE FIELD {i}:")
                    print(f"     id: {inp_id}")
                    print(f"     name: {inp_name}")
                    print(f"     placeholder: {inp_placeholder}")
                    print(f"     type: {inp_type}")
                    print(f"     value: {inp_value}")
                    duplicate_candidates.append(inp)
                    break

        if not duplicate_candidates:
            print("\n   No obvious duplicate fields found.")
            print("   Showing all input fields for reference:")

            for i, inp in enumerate(all_inputs[:20]):  # первые 20
                inp_id = inp.get_attribute('id') or ''
                inp_name = inp.get_attribute('name') or ''
                inp_placeholder = inp.get_attribute('placeholder') or ''

                if inp_id or inp_name or inp_placeholder:
                    print(f"   Input {i}: id='{inp_id}', name='{inp_name}', placeholder='{inp_placeholder}'")

        # Также ищем select элементы
        print("\n4. Searching for select fields...")
        all_selects = selenium.find_elements(By.CSS_SELECTOR, "select")
        print(f"   Total selects on page: {len(all_selects)}")

        for i, sel in enumerate(all_selects):
            sel_id = sel.get_attribute('id') or ''
            sel_name = sel.get_attribute('name') or ''

            if 'duplicate' in sel_id.lower() or 'duplicate' in sel_name.lower():
                print(f"   Found select that might be for duplicate: id='{sel_id}', name='{sel_name}'")

        # Закроем модальное окно если открыто
        try:
            close_btn = selenium.find_element(By.CSS_SELECTOR, ".btn-close, [data-dismiss='modal']")
            close_btn.click()
            time.sleep(0.5)
        except:
            pass

    def test_simple_duplication_effect(self, selenium: MiminetTester, network: MiminetTestNetwork):
        """Простой тест эффекта дублирования через прямое изменение данных"""
        print("\n=== DEBUG: Testing duplication effect directly ===")

        # Сначала получим базовое количество пакетов
        print("1. Running emulation with default settings...")
        packets = network.run_emulation()
        base_count = sum(len(group) for group in packets)
        print(f"   Baseline packet count: {base_count}")

        # Попробуем изменить duplicate через JavaScript напрямую
        print("\n2. Trying to set duplicate via JavaScript...")

        edge = network.edges[0]
        edge_id = edge['data']['id']

        # Проверим, есть ли глобальный объект edges
        edges_exists = selenium.execute_script("return typeof window.edges !== 'undefined'")
        print(f"   window.edges exists: {edges_exists}")

        if edges_exists:
            edges = selenium.execute_script("return window.edges")
            print(f"   Number of edges in window.edges: {len(edges) if edges else 0}")

            if edges and len(edges) > 0:
                print(f"   First edge in window.edges: {edges[0]}")

                # Попробуем добавить поле duplicate_percentage
                selenium.execute_script(f"""
                    const edge = window.edges.find(e => e.data.id === '{edge_id}');
                    if (edge) {{
                        edge.data.duplicate_percentage = 100;
                        console.log('Set duplicate_percentage to 100 for edge', '{edge_id}');
                    }}
                """)

                # Проверим, что поле добавилось
                edge_data = selenium.execute_script(f"""
                    const edge = window.edges.find(e => e.data.id === '{edge_id}');
                    return edge ? edge.data : null;
                """)

                print(f"   Edge data after setting duplicate: {edge_data}")

        # Запустим эмуляцию еще раз
        print("\n3. Running emulation after JavaScript modification...")
        packets = network.run_emulation()
        new_count = sum(len(group) for group in packets)
        print(f"   New packet count: {new_count}")

        # Просто сравним - если дублирование работает, должно быть больше пакетов
        print(f"   Comparison: base={base_count}, new={new_count}")

        if new_count > base_count:
            print("   SUCCESS: Packet count increased (duplication might be working)")
        else:
            print("   WARNING: Packet count didn't increase (duplication might not be working or not configured)")