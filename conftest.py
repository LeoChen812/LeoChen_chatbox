import time
from datetime import datetime
import allure
import pytest
import requests
from selenium import webdriver
# from selenium.common import WebDriverException
from selenium.webdriver import Safari
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.safari.options import Options as SafariOptions
# from urllib3.exceptions import MaxRetryError
from webdriver_manager.chrome import ChromeDriverManager


def pytest_addoption(parser):
    """
    Pytest initialization hook to allow custom arguments to be passed
    to set the scope to be used when running tests.
    Fixtures can have dynamic scope with the following declaration:

        @pytest.fixture(scope=determine_scope)
        def sample_fixture():
            ...

    Example usage:
        pytest --class path/to/test.py

    This will run fixtures with `scope=class`.
    Default will be `scope=function` if no argument is provided:
        pytest path/to/test.py
    """
    parser.addoption('--session', action='store_true', default=False)
    parser.addoption('--package', action='store_true', default=False)
    parser.addoption('--module', action='store_true', default=False)
    parser.addoption('--class', action='store_true', default=False)


def determine_scope(fixture_name, config) -> str:
    """
    Function to leverage Dynamic Scope usage on fixtyres, as opposed to hardcoded:
    https://docs.pytest.org/en/6.2.x/fixture.html#dynamic-scope
    :param fixture_name: fixtures which have param `scope=determine_scope`
    :param config: variable to be taken as argument when running the tests

    :return: which scope to use
    """

    if config.getoption("--session", None):
        return "session"
    if config.getoption("--package", None):
        return "package"
    if config.getoption("--module", None):
        return "module"
    if config.getoption("--class", None):
        return "class"
    return "function"


@pytest.fixture(params=["chrome"], scope=determine_scope)
def init_driver(request, default_chrome_options):
    """
    Main fixture for handling setup and teardown of webdrivers with dynamic scope

    :param request: The browser to use
    :param default_chrome_options: fixture setting default chrome options
    """

    print(f"\n--------------- Setting up {request.scope} scoped WebDriver for "
          f"{request.param} browser ---------------\n")
    web_driver = None
    if request.param == "chrome":
        web_driver = webdriver.Chrome(service=Service(ChromeDriverManager(version='114.0.5735.90').install()), options=default_chrome_options)
        # """
        # selenium grid: connect to vpn and go to http://192.168.188.17:4444 to check the test
        # """
        # web_driver = driver = webdriver.Remote(
        #     command_executor="http://192.168.188.17:4444",
        #     desired_capabilities={
        #         "browserName": "chrome",
        #         "platformName": "MAC",
        #         "se:noVncPort": 7900,
        #         "se:vncEnabled": True
        #     }
        # )
    if request.param == "safari":
        safari_options = SafariOptions()
        web_driver = Safari(options=safari_options)
        web_driver.maximize_window()  # maximize here since options don't work in MacOS
    if request.scope in ("function", "class"):
        request.cls.driver = web_driver
    yield web_driver
    print(f"\n--------------- Tearing Down {request.scope} scoped WebDriver for "
          f"{request.param} browser ---------------\n")
    web_driver.quit()


@pytest.fixture(scope=determine_scope)
def init_session(request):
    """
    Main fixture for handling setup and teardown of session with dynamic scope

    :param request: The session to use
    """
    session = requests.Session()
    if request.scope in ("function", "class"):
        request.cls.session = session
    yield session
    session.close()


@pytest.fixture(scope=determine_scope)
def default_chrome_options():
    """
    Fixture to set default chrome options.
    These options can be overridden by a custom fixture for specific tests,
    Example to override headless mode:

    @pytest.fixture(autouse=True)
    def custom_options(default_chrome_options):
        default_chrome_options.headless = False

    :return: ChromeOptions object
    """
    mobile_emulation = {
        "deviceName": "iPhone X"
    }
    options = webdriver.ChromeOptions()
    # options.add_experimental_option("mobileEmulation", mobile_emulation)
    # no need for it now, and it will make the chart test fail very often
    options.add_argument("--disable-popup-blocking")
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--start-maximized')
    options.add_argument('window-size=1920,1080')
    # options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('blink-settings=imagesEnabled=true')
    options.add_argument('--disable-gpu')
    return options


# set up a hook to be able to check if a test has failed
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Check if any test phase has failed (`setup`, `call`, `teardown`)
    Take a screenshot on failures
    https://stackoverflow.com/questions/60205391/how-to-capture-screenshot-on-test-case-failure-with-pytest
    """
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # set a report attribute for each phase of a call, which can be "setup", "call", "teardown"
    setattr(item, "rep_" + rep.when, rep)

    # Check if a test has failed during any phase
    # During `setup` phase
    if rep.when == "setup" and rep.outcome == "failed":
        print("Setting up test failed:", item.nodeid)

    # During `call` phase, i.e assertion errors
    if rep.when == "call" and rep.outcome == "failed":

        # Take a screenshot if it's a Selenium WebDriver test
        if "init_driver" in item.funcargs.keys():
            driver = item.funcargs['init_driver']

            # Take screenshot and store locally in the same folder of test module
            # Uncomment to debug visually when developing automations
            # take_screenshot(driver, item.nodeid)

            # Take screenshot and attach to allure report
            allure.attach(driver.get_screenshot_as_png(), name="test_fail_screenshot")
            print("Executing test failed:", item.nodeid)

        # Check if failed class/test is marked as `incremental`, i.e `@pytest.mark.incremental`
        if "incremental" in item.keywords:
            if call.excinfo is not None:
                parent = item.parent
                parent._previous_failed = item

    # During `teardown` phase
    if rep.when == "teardown" and rep.outcome == "failed":
        print("Tearing down test failed:", item.nodeid)


def pytest_runtest_call(item):
    """
    On test setup phase check if previous one has failed and skip remaining tests.
    NOTE: This should only be used in exceptional cases, i.e having an API
    generate data which needs to be tested in the same session between several
    tests in the same suite.
    Tests should `always` be as independent of each other as possible.
    https://stackoverflow.com/questions/12411431/how-to-skip-the-rest-of-tests-in-the-class-if-one-has-failed
    """
    previous_failed = getattr(item.parent, "_previous_failed", None)

    # Skip tests marked as incremental if previous test has failed
    if previous_failed is not None and "incremental" in item.keywords:
        pytest.skip(f"Skipping current test after failure of the previous test: {previous_failed.name}")


def take_screenshot(driver, nodeid):
    """
    Take a screenshot with the name of the test, date and time
    """
    time.sleep(1)
    node = nodeid.split("::")
    test_name = node[1] + "::" + node[2]
    file_name = f'{test_name}_{datetime.today().strftime("%Y-%m-%d_%H:%M")}.png'
    driver.save_screenshot(file_name)
