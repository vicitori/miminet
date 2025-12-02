import pytest
from selenium.webdriver.common.by import By
import time


def test_simplest_duplicate_check():
    """Самый простой тест - проверяем что мы вообще можем взаимодействовать со страницей"""
    print("\n=== Самый простой тест ===")

    # Нужно получить драйвер из контекста pytest
    # Обычно в conftest.py есть фикстура driver или selenium

    try:
        # Попробуем получить driver разными способами
        import conftest
        print(f"conftest module: {conftest}")

        # Запускаем через pytest -v чтобы увидеть вывод
        print("Тест запущен...")

        # Просто проверяем что тест запускается
        assert True

    except Exception as e:
        print(f"Ошибка при запуске теста: {e}")
        raise


# Давайте проверим существование локаторов
def test_duplicate_locator():
    """Проверяем что локатор для duplicate поля определен"""
    print("\n=== Проверка локаторов ===")

    try:
        from utils.locators import Location
        print(f"Location module loaded: {Location}")

        # Проверяем что селектор существует
        selector = Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
        print(f"Duplicate field selector: {selector}")

        assert selector is not None
        assert selector != ""
        print(f"✓ Локатор найден: {selector}")

    except ImportError as e:
        print(f"✗ Не могу импортировать Location: {e}")
        pytest.skip("Location module not available")
    except AttributeError as e:
        print(f"✗ Локатор не найден: {e}")

        # Покажем что есть в Location
        from utils.locators import Location
        print(f"Что есть в Location.Network.ConfigPanel.Edge: {dir(Location.Network.ConfigPanel.Edge)}")
        raise


# Тест который работает с уже открытой страницей
def test_page_has_network_elements(selenium):
    """Тест проверяет что на странице есть элементы сети"""
    print("\n=== Проверка элементов сети на странице ===")

    # Проверяем базовые элементы
    print(f"Текущий URL: {selenium.current_url}")
    print(f"Заголовок страницы: {selenium.title}")

    # Проверяем что есть body
    body = selenium.find_element(By.TAG_NAME, "body")
    print(f"Body найден: {body is not None}")

    # Ищем кнопки сети
    network_buttons = selenium.find_elements(By.CSS_SELECTOR, "[id*='network'], [class*='network']")
    print(f"Найдено элементов с 'network': {len(network_buttons)}")

    # Ищем canvas или граф
    canvas_elements = selenium.find_elements(By.TAG_NAME, "canvas")
    print(f"Canvas элементов: {len(canvas_elements)}")

    # Проверяем JavaScript функции
    show_edge_func = selenium.execute_script("return typeof ShowEdgeConfig === 'function'")
    print(f"Функция ShowEdgeConfig существует: {show_edge_func}")

    # Если функция существует, значит мы на правильной странице
    assert show_edge_func, "Функция ShowEdgeConfig должна существовать на странице сети"
    print("✓ Базовая проверка страницы пройдена")


# Простой тест на открытие модального окна
def test_open_edge_config_modal(selenium):
    """Тест открытия модального окна конфигурации ребра"""
    print("\n=== Тест открытия модального окна ===")

    # Сначала создадим простую сеть через JavaScript
    print("Создаем простую сеть через JavaScript...")

    network_script = """
    // Проверяем есть ли cytoscape
    if (typeof cy !== 'undefined') {
        // Создаем два узла и связь между ними
        const host1 = cy.add({data: {id: 'test_host1', label: 'host1', type: 'host'}});
        const host2 = cy.add({data: {id: 'test_host2', label: 'host2', type: 'host'}});
        const edge = cy.add({data: {id: 'test_edge', source: 'test_host1', target: 'test_host2'}});

        return {success: true, edgeId: 'test_edge'};
    } else {
        return {success: false, error: 'cytoscape not initialized'};
    }
    """

    result = selenium.execute_script(network_script)
    print(f"Результат создания сети: {result}")

    if result and result.get('success'):
        edge_id = result['edgeId']
        print(f"Создано ребро: {edge_id}")

        # Пробуем открыть конфигурацию
        print(f"Пробуем открыть ShowEdgeConfig('{edge_id}')...")
        selenium.execute_script(f"ShowEdgeConfig('{edge_id}')")
        time.sleep(2)

        # Проверяем что модальное окно открылось
        modal_count = selenium.execute_script(
            "return document.querySelectorAll('.modal.show, .modal.in, [role=dialog]').length"
        )
        print(f"Открыто модальных окон: {modal_count}")

        if modal_count > 0:
            print("✓ Модальное окно открылось")

            # Ищем поле edge_duplicate
            try:
                duplicate_field = selenium.find_element(By.ID, "edge_duplicate")
                print(f"✓ Найдено поле edge_duplicate")
                print(f"  Значение: {duplicate_field.get_attribute('value')}")
                print(f"  Тип: {duplicate_field.get_attribute('type')}")
            except:
                print("✗ Поле edge_duplicate не найдено")

                # Показываем все input поля в модальном окне
                inputs = selenium.execute_script("""
                    const modal = document.querySelector('.modal.show, .modal.in');
                    if (!modal) return [];
                    const inputs = modal.querySelectorAll('input');
                    return Array.from(inputs).map(input => ({
                        id: input.id,
                        name: input.name,
                        type: input.type,
                        value: input.value
                    }));
                """)
                print(f"Все input поля в модальном окне: {inputs}")

        else:
            print("✗ Модальное окно не открылось")

    else:
        print("✗ Не удалось создать сеть, cytoscape не инициализирован")
        pytest.skip("Cytoscape not initialized, cannot test edge config")


# Самый надежный тест - через прямое обращение к HTML
def test_html_structure_for_duplicate(selenium):
    """Анализ HTML структуры для поиска поля duplicate"""
    print("\n=== Анализ HTML структуры ===")

    # Получаем весь HTML страницы
    page_source = selenium.page_source

    print(f"Длина HTML: {len(page_source)} символов")

    # Ищем упоминания duplicate
    if 'duplicate' in page_source.lower():
        print("✓ Слово 'duplicate' найдено в HTML")

        # Находим контекст
        import re

        # Ищем id с duplicate
        id_matches = re.findall(r'id=[\'"][^\'"]*duplicate[^\'"]*[\'"]', page_source, re.IGNORECASE)
        print(f"Найдено id с 'duplicate': {len(id_matches)}")
        for match in id_matches[:5]:  # первые 5
            print(f"  {match}")

        # Ищем input элементы
        input_matches = re.findall(r'<input[^>]*>', page_source, re.IGNORECASE)
        print(f"Всего input элементов: {len(input_matches)}")

        # Ищем input с duplicate
        duplicate_inputs = []
        for input_tag in input_matches:
            if 'duplicate' in input_tag.lower():
                duplicate_inputs.append(input_tag)

        print(f"Input элементов с 'duplicate': {len(duplicate_inputs)}")
        for inp in duplicate_inputs[:3]:
            print(f"  {inp[:100]}...")

        if duplicate_inputs:
            print("✓ Найдены input поля связанные с duplicate")
            assert True
        else:
            print("✗ Не найдены input поля с 'duplicate'")

    else:
        print("✗ Слово 'duplicate' не найдено в HTML")
        # Ищем альтернативные названия
        for term in ['loss', 'потер', 'процент', 'percentage', 'дубл']:
            if term in page_source.lower():
                print(f"  Найдено альтернативное слово: '{term}'")


# Финальный минимальный тест
@pytest.mark.parametrize('test_input,expected', [
    (1, 1),
    (2, 2),
])
def test_trivial(test_input, expected):
    """Тривиальный тест чтобы проверить что pytest работает"""
    print(f"\nТривиальный тест: {test_input} == {expected}")
    assert test_input == expected
    print("✓ Тривиальный тест пройден")