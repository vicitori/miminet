import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def test_create_network_and_check_duplicate(selenium):
    """Создаем сеть и проверяем поле duplicate"""
    print("\n=== Тест: Создание сети и проверка duplicate ===")

    # 1. Переходим на страницу создания сети
    print("1. Переход на страницу создания сети...")
    selenium.get("http://172.18.0.2/web_network")
    time.sleep(2)

    print(f"Текущий URL: {selenium.current_url}")
    print(f"Заголовок: {selenium.title}")

    # 2. Проверяем что мы на странице сети
    assert "web_network" in selenium.current_url, "Должны быть на странице сети"

    # 3. Проверяем что cytoscape инициализирован
    print("2. Проверка инициализации cytoscape...")
    cytoscape_ready = selenium.execute_script("return typeof cy !== 'undefined'")
    print(f"Cytoscape инициализирован: {cytoscape_ready}")

    if not cytoscape_ready:
        print("Ожидание инициализации cytoscape...")
        time.sleep(3)
        cytoscape_ready = selenium.execute_script("return typeof cy !== 'undefined'")
        print(f"Cytoscape после ожидания: {cytoscape_ready}")

    # 4. Создаем простую сеть через UI
    print("3. Создание простой сети...")

    # Ищем кнопку добавления хоста
    try:
        add_host_btn = WebDriverWait(selenium, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Хост') or contains(text(), 'Host')]"))
        )
        add_host_btn.click()
        print("Кнопка 'Хост' найдена и нажата")
        time.sleep(1)
    except:
        print("Кнопка 'Хост' не найдена, пробуем через JavaScript")
        # Альтернативный способ
        selenium.execute_script("""
            // Ищем любую кнопку добавления узла
            const buttons = document.querySelectorAll('button');
            for (const btn of buttons) {
                if (btn.textContent.includes('Хост') || btn.textContent.includes('Host')) {
                    btn.click();
                    break;
                }
            }
        """)
        time.sleep(1)

    # 5. Проверяем что узел добавлен
    node_count = selenium.execute_script("return typeof cy !== 'undefined' ? cy.nodes().length : 0")
    print(f"Узлов в сети: {node_count}")

    if node_count == 0:
        # Добавляем узел через JavaScript
        print("Добавляем узел через JavaScript...")
        selenium.execute_script("""
            if (typeof cy !== 'undefined') {
                cy.add({
                    data: { id: 'test_host_1', label: 'host1', type: 'host' },
                    position: { x: 100, y: 100 }
                });
                console.log('Добавлен узел test_host_1');
            }
        """)
        time.sleep(1)

    # 6. Добавляем второй узел и связь
    print("4. Добавление второго узла и связи...")
    selenium.execute_script("""
        if (typeof cy !== 'undefined') {
            // Второй узел
            cy.add({
                data: { id: 'test_host_2', label: 'host2', type: 'host' },
                position: { x: 300, y: 100 }
            });

            // Связь между узлами
            cy.add({
                data: { 
                    id: 'test_edge_1', 
                    source: 'test_host_1', 
                    target: 'test_host_2',
                    label: ''
                }
            });

            console.log('Создана сеть: 2 хоста и связь между ними');
        }
    """)
    time.sleep(1)

    # 7. Проверяем создание
    edge_count = selenium.execute_script("return typeof cy !== 'undefined' ? cy.edges().length : 0")
    print(f"Создано связей: {edge_count}")

    if edge_count == 0:
        pytest.skip("Не удалось создать связь между узлами")

    # 8. Пробуем открыть конфигурацию связи
    print("5. Открытие конфигурации связи...")

    # Получаем ID первой связи
    edge_id = selenium.execute_script("""
        if (typeof cy !== 'undefined' && cy.edges().length > 0) {
            return cy.edges()[0].id();
        }
        return null;
    """)

    print(f"ID связи: {edge_id}")

    if not edge_id:
        pytest.skip("Не удалось получить ID связи")

    # Открываем конфигурацию
    selenium.execute_script(f"ShowEdgeConfig('{edge_id}')")
    time.sleep(2)

    # 9. Проверяем что модальное окно открылось
    print("6. Проверка модального окна...")
    modal_visible = selenium.execute_script("""
        const modal = document.querySelector('.modal.show, .modal.in');
        return modal && modal.offsetParent !== null;
    """)

    print(f"Модальное окно открыто: {modal_visible}")

    if not modal_visible:
        print("Пробуем найти модальное окно другими способами...")
        modals = selenium.find_elements(By.CSS_SELECTOR, ".modal, [role='dialog']")
        print(f"Найдено модальных окон: {len(modals)}")

        for i, modal in enumerate(modals):
            print(f"Модальное окно {i}: class='{modal.get_attribute('class')}', style='{modal.get_attribute('style')}'")

    # 10. Ищем поле edge_duplicate
    print("7. Поиск поля edge_duplicate...")

    try:
        # Сначала ждем появления модального окна
        WebDriverWait(selenium, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".modal-content"))
        )

        # Ищем поле внутри модального окна
        duplicate_field = selenium.find_element(By.ID, "edge_duplicate")
        print(f"✓ Найдено поле edge_duplicate!")
        print(f"  ID: {duplicate_field.get_attribute('id')}")
        print(f"  Тип: {duplicate_field.get_attribute('type')}")
        print(f"  Значение: {duplicate_field.get_attribute('value')}")
        print(f"  Placeholder: {duplicate_field.get_attribute('placeholder')}")

        # Проверяем что это поле number
        assert duplicate_field.get_attribute('type') == 'number', "Поле должно быть типа number"
        assert duplicate_field.get_attribute('id') == 'edge_duplicate', "ID должен быть edge_duplicate"

        # 11. Тестируем установку значения
        print("8. Тестирование установки значения...")

        # Запоминаем текущее значение
        current_value = duplicate_field.get_attribute('value') or '0'
        print(f"Текущее значение: {current_value}")

        # Устанавливаем новое значение
        duplicate_field.clear()
        duplicate_field.send_keys("75")

        # Проверяем установку
        new_value = duplicate_field.get_attribute('value')
        print(f"Новое значение: {new_value}")
        assert new_value == "75", f"Ожидалось 75, получено {new_value}"

        # 12. Закрываем модальное окно
        print("9. Закрытие модального окна...")
        close_btn = selenium.find_element(By.CSS_SELECTOR, ".btn-close, [data-dismiss='modal']")
        close_btn.click()
        time.sleep(1)

        print("✓ Тест успешно завершен!")

    except Exception as e:
        print(f"✗ Ошибка: {e}")

        # Для отладки покажем все input поля на странице
        print("\nОтладка: все input поля на странице:")
        all_inputs = selenium.find_elements(By.TAG_NAME, "input")
        print(f"Всего input полей: {len(all_inputs)}")

        for i, inp in enumerate(all_inputs[:10]):  # первые 10
            inp_id = inp.get_attribute('id') or 'NO_ID'
            inp_type = inp.get_attribute('type') or 'NO_TYPE'
            inp_value = inp.get_attribute('value') or 'NO_VALUE'
            print(f"  Input {i}: id='{inp_id}', type='{inp_type}', value='{inp_value}'")

        # Покажем HTML модального окна если есть
        modal_html = selenium.execute_script("""
            const modal = document.querySelector('.modal-content');
            return modal ? modal.outerHTML.substring(0, 500) : 'Модальное окно не найдено';
        """)
        print(f"\nHTML модального окна (первые 500 символов):\n{modal_html}")

        raise


def test_duplicate_with_existing_network_class():
    """Тест с использованием существующего класса MiminetTestNetwork"""
    print("\n=== Тест с MiminetTestNetwork ===")

    from conftest import MiminetTester
    from utils.networks import NodeType, MiminetTestNetwork

    # Получаем selenium из глобального контекста
    import conftest
    selenium = conftest.selenium

    print(f"Используем selenium: {selenium}")
    print(f"Текущий URL: {selenium.current_url}")

    # Если мы не на странице сети, переходим на нее
    if "web_network" not in selenium.current_url:
        print("Переход на страницу создания сети...")
        selenium.get("http://172.18.0.2/web_network")
        time.sleep(3)

    # Создаем сеть через MiminetTestNetwork
    print("Создание сети через MiminetTestNetwork...")
    network = MiminetTestNetwork(selenium)

    try:
        # Добавляем узлы
        host1_id = network.add_node(NodeType.Host, x=100, y=100)
        host2_id = network.add_node(NodeType.Host, x=300, y=100)

        print(f"Созданы узлы: {host1_id}, {host2_id}")

        # Добавляем связь
        edge_id = network.add_edge(host1_id, host2_id)
        print(f"Создана связь: {edge_id}")

        # Проверяем что связь создана
        edge_count = selenium.execute_script("return cy.edges().length")
        print(f"Всего связей в cytoscape: {edge_count}")

        # Открываем конфигурацию связи
        print(f"Открытие конфигурации для связи {edge_id}...")

        # Получаем объект edge
        edge = None
        for e in network.edges:
            if e['data']['id'] == edge_id:
                edge = e
                break

        if edge:
            print(f"Найден edge объект: {edge}")

            # Открываем конфигурацию
            network.open_edge_config(edge)
            time.sleep(2)

            # Ищем поле duplicate
            try:
                from selenium.webdriver.common.by import By
                duplicate_field = selenium.find_element(By.ID, "edge_duplicate")
                print(f"✓ Найдено поле edge_duplicate!")

                # Проверяем базовые свойства
                assert duplicate_field.get_attribute('id') == 'edge_duplicate'
                assert duplicate_field.get_attribute('type') == 'number'

                print(f"  Тип: {duplicate_field.get_attribute('type')}")
                print(f"  Значение: {duplicate_field.get_attribute('value')}")

                # Закрываем модальное окно
                close_btn = selenium.find_element(By.CSS_SELECTOR, ".btn-close")
                close_btn.click()
                time.sleep(1)

            except Exception as e:
                print(f"✗ Ошибка при поиске поля: {e}")

                # Отладка
                modal_html = selenium.execute_script("""
                    const modal = document.querySelector('.modal-content');
                    return modal ? modal.outerHTML.substring(0, 300) : 'Нет модального окна';
                """)
                print(f"HTML модального окна: {modal_html}")

                # Закрываем если открыто
                selenium.execute_script("""
                    const closeBtn = document.querySelector('.btn-close');
                    if (closeBtn) closeBtn.click();
                """)

                raise
        else:
            print("✗ Не найден edge объект")

    finally:
        # Очищаем
        print("Очистка сети...")
        network.delete()
        time.sleep(1)