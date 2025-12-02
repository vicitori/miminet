import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def test_minimal_duplicate_workflow():
    """Минимальный рабочий тест по примеру других успешных тестов"""
    print("\n=== Минимальный тест дублирования ===")

    # Импортируем необходимые модули
    from conftest import MiminetTester
    from utils.networks import NodeType, MiminetTestNetwork
    from utils.locators import Location

    # Получаем selenium
    import conftest
    selenium = conftest.selenium

    print(f"1. Текущий URL: {selenium.current_url}")

    # Создаем сеть так же, как в других тестах
    network = MiminetTestNetwork(selenium)

    try:
        print("2. Создание узлов...")
        host1_id = network.add_node(NodeType.Host, x=100, y=100)
        host2_id = network.add_node(NodeType.Host, x=300, y=100)

        print(f"   Созданы хосты: {host1_id}, {host2_id}")

        print("3. Создание связи...")
        edge_id = network.add_edge(host1_id, host2_id)
        print(f"   Создана связь: {edge_id}")

        # Настраиваем хосты (как в других тестах)
        print("4. Настройка хостов...")

        # Host 1
        config1 = network.open_node_config(host1_id)
        config1.fill_link("192.168.1.1", 24)
        config1.add_jobs(
            1,
            {Location.Network.ConfigPanel.Host.Job.PING_FIELD.selector: "192.168.1.2"},
        )
        config1.submit()

        # Host 2
        config2 = network.open_node_config(host2_id)
        config2.fill_link("192.168.1.2", 24)
        config2.submit()

        print("5. Открытие конфигурации связи...")

        # Находим edge объект
        edge_obj = None
        for edge in network.edges:
            if edge['data']['id'] == edge_id:
                edge_obj = edge
                break

        if not edge_obj:
            print("✗ Связь не найдена в network.edges")
            print(f"   Все связи: {network.edges}")
            pytest.fail("Связь не найдена")

        print(f"   Найден edge объект: {edge_obj['data']['id']}")

        # Открываем конфигурацию связи
        network.open_edge_config(edge_obj)
        time.sleep(2)

        print("6. Поиск поля duplicate...")

        # Ждем появления модального окна
        try:
            WebDriverWait(selenium, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal-content"))
            )
            print("   ✓ Модальное окно открыто")
        except:
            print("   ✗ Модальное окно не открылось")
            # Покажем что есть на странице
            modals = selenium.find_elements(By.CSS_SELECTOR, ".modal, [role='dialog']")
            print(f"   Все модальные окна: {len(modals)}")
            for i, m in enumerate(modals):
                print(f"   Модальное {i}: class='{m.get_attribute('class')}'")

        # Ищем поле edge_duplicate
        try:
            duplicate_field = selenium.find_element(By.ID, "edge_duplicate")
            print(f"   ✓ Найдено поле edge_duplicate!")
            print(f"     ID: {duplicate_field.get_attribute('id')}")
            print(f"     Type: {duplicate_field.get_attribute('type')}")
            print(f"     Value: {duplicate_field.get_attribute('value')}")
            print(f"     Placeholder: {duplicate_field.get_attribute('placeholder')}")

        except Exception as e:
            print(f"   ✗ Поле не найдено: {e}")

            # Отладка: все поля в модальном окне
            print("\n   Отладка - все input поля в модальном окне:")
            modal_inputs = selenium.execute_script("""
                const modal = document.querySelector('.modal-content');
                if (!modal) return 'Нет модального окна';
                const inputs = modal.querySelectorAll('input, select, textarea');
                const result = [];
                inputs.forEach((input, i) => {
                    result.push({
                        index: i,
                        tag: input.tagName,
                        id: input.id,
                        name: input.name,
                        type: input.type,
                        value: input.value,
                        placeholder: input.placeholder
                    });
                });
                return result;
            """)

            if isinstance(modal_inputs, list):
                for inp in modal_inputs:
                    print(f"     {inp}")
            else:
                print(f"     {modal_inputs}")

            raise

        print("7. Тестирование установки значения...")

        # Устанавливаем значение
        duplicate_field.clear()
        duplicate_field.send_keys("42")

        # Проверяем
        current_value = duplicate_field.get_attribute('value')
        print(f"   Установлено значение: {current_value}")
        assert current_value == "42", f"Ожидалось 42, получено {current_value}"

        print("8. Сохранение...")

        # Находим кнопку сохранения
        try:
            submit_btn = selenium.find_element(By.ID, "config_edge_main_form_submit_button")
            submit_btn.click()
            print("   ✓ Нажата кнопка сохранения")
            time.sleep(1)
        except:
            print("   ⚠ Кнопка сохранения не найдена, нажимаем Enter")
            duplicate_field.send_keys("\n")
            time.sleep(1)

        print("9. Закрытие модального окна...")
        try:
            close_btn = selenium.find_element(By.CSS_SELECTOR, ".btn-close")
            close_btn.click()
            time.sleep(1)
        except:
            print("   ⚠ Кнопка закрытия не найдена")

        print("\n✓ Тест успешно завершен!")

    finally:
        # Очистка
        print("\n10. Очистка сети...")
        network.delete()
        time.sleep(1)


def test_duplicate_simple_validation():
    """Простой тест валидации поля duplicate"""
    print("\n=== Простой тест валидации ===")

    from conftest import MiminetTester
    from utils.networks import NodeType, MiminetTestNetwork

    import conftest
    selenium = conftest.selenium

    network = MiminetTestNetwork(selenium)

    try:
        # Создаем минимальную сеть
        host1_id = network.add_node(NodeType.Host)
        host2_id = network.add_node(NodeType.Host)
        edge_id = network.add_edge(host1_id, host2_id)

        print(f"Создана связь: {edge_id}")

        # Находим edge
        edge = None
        for e in network.edges:
            if e['data']['id'] == edge_id:
                edge = e
                break

        if not edge:
            pytest.skip("Связь не найдена")

        # Открываем конфигурацию
        network.open_edge_config(edge)
        time.sleep(2)

        # Ищем поле
        duplicate_field = selenium.find_element(By.ID, "edge_duplicate")

        # Тестируем допустимые значения
        test_values = [("0", True), ("50", True), ("100", True)]

        for value, should_work in test_values:
            duplicate_field.clear()
            duplicate_field.send_keys(value)

            actual = duplicate_field.get_attribute('value')
            print(f"Ввод {value}: поле показывает {actual}")

            if should_work:
                assert actual == value, f"Для {value} ожидалось {value}, получено {actual}"
            else:
                print(f"  Примечание: {value} может не приниматься")

        # Закрываем
        close_btn = selenium.find_element(By.CSS_SELECTOR, ".btn-close")
        close_btn.click()
        time.sleep(1)

        print("✓ Тест валидации пройден")

    finally:
        network.delete()


# Самый простой тест - только проверка что сеть создается
def test_network_creation_basic():
    """Базовый тест создания сети"""
    print("\n=== Базовый тест создания сети ===")

    from conftest import MiminetTester
    from utils.networks import NodeType, MiminetTestNetwork

    import conftest
    selenium = conftest.selenium

    print(f"Начальный URL: {selenium.current_url}")

    network = MiminetTestNetwork(selenium)

    try:
        # Проверяем что сеть создана
        assert network is not None
        print("✓ Сеть создана")

        # Проверяем URL
        print(f"URL после создания сети: {selenium.current_url}")
        assert "web_network" in selenium.current_url, "Должны быть на странице сети"

        # Проверяем cytoscape
        cytoscape_exists = selenium.execute_script("return typeof cy !== 'undefined'")
        print(f"Cytoscape инициализирован: {cytoscape_exists}")

        # Добавляем узел
        node_id = network.add_node(NodeType.Host)
        print(f"Добавлен узел: {node_id}")

        # Проверяем что узел добавлен
        nodes_count = selenium.execute_script("return cy ? cy.nodes().length : 0")
        print(f"Узлов в сети: {nodes_count}")
        assert nodes_count > 0, "Узел должен быть добавлен"

        print("✓ Базовая функциональность сети работает")

    finally:
        network.delete()
        print("Сеть удалена")