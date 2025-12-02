from selenium.webdriver.common.by import By
from utils.locators import Location
from conftest import MiminetTester, HOME_PAGE
from miminet_test_network import MiminetTestNetwork


def test_edge_duplicate_field(selenium: MiminetTester):
    """Проверяет работу поля дублирования пакетов в конфиге ребра."""
    net = MiminetTestNetwork(selenium)

    # Добавим два хоста
    h1 = net.add_node(MiminetTestNetwork.__class__.Host)
    h2 = net.add_node(MiminetTestNetwork.__class__.Host)

    # Соединим их
    edge_index = net.add_edge(h1, h2)

    # Откроем конфиг ребра
    edge = net.edges[edge_index]
    net.open_edge_config(edge)

    # Поле дублирования доступно в Location.Network.ConfigPanel.Edge
    dup_selector = Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector

    # Найдём поле и введём значение
    dup_el = selenium.find_element(By.CSS_SELECTOR, dup_selector)
    dup_el.clear()
    dup_el.send_keys('42')

    # Сохраним
    submit_selector = Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector
    selenium.find_element(By.CSS_SELECTOR, submit_selector).click()

    # После сохранения ожидаем, что у ребра в глобальной переменной edges появилось duplicate_percentage
    selenium.wait_for(lambda _: 'duplicate_percentage' in net.edges[edge_index]['data'])
    assert net.edges[edge_index]['data']['duplicate_percentage'] == '42'


def test_edge_duplicate_sent_on_post(selenium: MiminetTester):
    """Проверяет, что при отправке на бэк-энд отправляются данные с полем duplicate_percentage."""
    net = MiminetTestNetwork(selenium)

    h1 = net.add_node(MiminetTestNetwork.__class__.Host)
    h2 = net.add_node(MiminetTestNetwork.__class__.Host)
    edge_index = net.add_edge(h1, h2)

    edge = net.edges[edge_index]
    net.open_edge_config(edge)

    dup_selector = Location.Network.ConfigPanel.Edge.DUPLICATE_FIELD.selector
    dup_el = selenium.find_element(By.CSS_SELECTOR, dup_selector)
    dup_el.clear()
    dup_el.send_keys('7')

    submit_selector = Location.Network.ConfigPanel.Edge.SUBMIT_BUTTON.selector
    selenium.find_element(By.CSS_SELECTOR, submit_selector).click()

    # Симулируем отправку на бэк
    # Предполагается, что функция PostNodesEdges формирует данные в переменной lastPostedData
    selenium.execute_script("PostNodesEdges(); window.lastPostedData = window.__last_posted__; ")

    posted = selenium.execute_script('return window.lastPostedData')
    # Проверим, что в отправленных данных есть duplicate_percentage = 7
    found = False
    for e in posted.get('edges', []):
        if e.get('data', {}).get('duplicate_percentage') == '7':
            found = True
            break
    assert found, 'duplicate_percentage not present in posted edges'

