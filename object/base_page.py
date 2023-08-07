"""
BasePage object class and generic methods only
"""

import os
import pprint
import sys
import time

from selenium.common import TimeoutException, NoSuchElementException, ElementNotVisibleException, \
    ElementClickInterceptedException, ElementNotInteractableException, UnexpectedAlertPresentException
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.ui import Select

import object.javascript_functions


class BasePage:
    """
    BasePage class to contain commonly used page interactions to avoid code repeatability
    and follow DRY principle
    """

    # BASE PAGE CONSTRUCTOR

    def __init__(self, driver: WebDriver, url=None, title=None, pybug=None):
        """
        Main constructor for all page objects, with attributes common to any page

        :param driver: WebDriver instance used by the page instance
        :param url: URL of the page
        :param title: Page Title
        :param pybug: Logger for the page object
        """
        self.driver = driver
        self.url = url
        self.title = title
        if pybug:
            self.pybug = pybug
        else:
            self.pybug = pprint.pprint
        self.action = ActionChains(self.driver)

    # GENERIC METHODS

    def go_to_link(self, url: str, nuke: bool = False) -> None:
        """
        Method to go to a specific `url`.

        :param url: URL as `str` to be passed
        :param nuke: Delete the whole page before navigating to URL.
                     Last resort workaround for Chrome's `beforeunload` event alerts
        """
        if nuke:
            self.nuke_page_body()

        try:
            self.driver.get(url)
            self.override_beforeunload_events()
        except UnexpectedAlertPresentException:
            error = self.get_exception()
            self.meta_raise(error)

    def refresh_page(self, nuke: bool = False):
        """
        Refresh current page.

        :param nuke: Delete the whole page before navigating to URL.
             Last resort workaround for Chrome's `beforeunload` event alerts
        """
        if nuke:
            self.nuke_page_body()

        try:
            self.driver.refresh()
            self.override_beforeunload_events()
        except UnexpectedAlertPresentException:
            error = self.get_exception()
            self.meta_raise(error)

    def override_beforeunload_events(self):
        """
        Javascript functions to override `beforeunload` events, to avoid throwing
        `UnexpectedAlertPresentException` when changing URL or refreshing page.
        References:
        https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeunload_event
        https://sqa.stackexchange.com/questions/33301/how-to-handle-browser-closing-popup
        https://stackoverflow.com/questions/55587025/how-to-disable-a-reload-site-changes-you-made-may-not-be-saved-popup-for-pyt
        """
        # Deal with `window.addEventListener('beforeunload', ...)`
        self.driver.execute_script(
            "Object.defineProperty(BeforeUnloadEvent.prototype, 'returnValue', "
            "{ get:function(){}, set:function(){} });")
        # Deal with `window.onbeforeunload`
        self.driver.execute_script("window.onbeforeunload = function() {};")

    def nuke_page_body(self):
        """
        Last resort workaround to deal with `beforeunload` browsers' alerts when
        changing url or refreshing page.
        Should be used before `goto_link` or `refresh_page` to prevent specific
        products/pages from triggering `beforeunload` functions.
        """
        self.driver.execute_script(
            "document.querySelector('html').parentNode.removeChild(document.querySelector('html'));")

    def get_page_title(self) -> str:
        """
        Method to return the title of current webpage

        :return: Page title text
        """
        return self.driver.title

    def click_element(self, element: tuple | WebElement, timeout: float = 15) -> None:
        """
        Method to click() a WebElement

        :param element: WebElement's locator as a `tuple`
        :param timeout: Amount of time to pass to `wait_and_get_element`
        """
        try:
            if isinstance(element, tuple):
                self.wait_and_get_element(element, timeout).click()
            else:
                element.click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            if isinstance(element, tuple):
                element = self.wait_and_get_element(element, timeout)
            self.action.click(element).perform()

    def clear_text_field(self, element: tuple, timeout: float = 10) -> None:
        """
        Method to clear() a WebElement's text

        :param element: WebElement's locator as a `tuple`
        :param timeout: Amount of time to pass to `wait_and_get_element`
        """
        self.wait_and_get_element(element, timeout).clear()

    def clear_text_by_keyboard(self, element: tuple, timeout: float = 10) -> None:
        """
         Method to clear WebElement's text by keyboard behavior

        :param element: WebElement `tuple` to interact with
        :param timeout: Amount of time to pass to `wait_and_get_element`
        """
        for _ in self.wait_and_get_element(element, timeout).get_attribute('value'):
            self.wait_and_get_element(element, timeout).send_keys(Keys.BACKSPACE)

    def set_text_field(self, element: tuple, text, timeout: float = 10) -> None:
        """
        Method to send_keys() to a WebElement

        :param element: WebElement's locator as a `tuple`
        :param timeout: Amount of time to pass to `wait_and_get_element`
        :param text: Input text
        """
        self.clear_text_field(element, timeout)
        self.driver.find_element(*element).send_keys(text)

    def get_element_text(self, element: tuple | WebElement, timeout: float = 10) -> str:
        """
        Method to get text from a WebElement

        :param element: WebElement's locator as a `tuple`
        :param timeout: Amount of time to pass to `wait_and_get_element`
        :return: Text of WebElement
        """
        return self.wait_and_get_element(element, timeout).text

    def get_element_inner_text(self, element: tuple, timeout: float = 10) -> str:
        """
        Method to get text from a WebElement

        :param element: WebElement's locator as a `tuple`
        :param timeout: Amount of time to pass to `wait_and_get_element`
        :return: Text of WebElement
        """
        return self.wait_and_get_element(element, timeout).get_attribute('innerText')

    def get_text_and_styles(self, element: tuple, timeout: float = 15,
                            css_to_get: tuple = ("font-family", "font-size", "font-weight", "color")) -> (str, dict):
        """
        Get element's text and common/most important CSS

        :returns: WebElement's text and respective css properties
        """
        element = self.wait_and_get_element(element, timeout)
        return element.text, self.get_css_as_dict(element, css_to_get)

    def wait_and_get_element(self, element: tuple, timeout: float = 15) -> WebElement:
        """
        Method to deal with waiting for an element and finding it in the DOM.

        :param element: WebElement's locator as a `tuple`
        :param timeout: Time in seconds we want to wait when locating elements
        :return: WebElement to be interacted with
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.all_of(
                    EC.visibility_of_element_located(element),
                    EC.presence_of_element_located(element),
                )
            )
            return self.driver.find_element(*element)
        except (TimeoutException, NoSuchElementException,
                ElementNotVisibleException):
            error = self.get_exception()
            self.meta_raise(error)

    def wait_and_check_url(self, target_url, condition: str = "to_be",
                           timeout: float = 10,
                           error_message: str = "Wrong URL redirect"):
        """
        Generic method to wait for and assert for URL redirects.

        :param target_url: URL to compare to
        :param condition: ExpectedConditions to use for URL verification.
                          Default = `to_be` -> https://selenium-python.readthedocs.io/api.html?highlight=url_to_be#selenium.webdriver.support.expected_conditions.url_to_be
        :param timeout: How long to wait in seconds. Default = 10
        :param error_message: Error message to pass to assertion.
                              Default = `Wrong URL redirect`
        """
        wait = WebDriverWait(self.driver, timeout)
        try:
            if condition == "to_be":
                wait.until(EC.url_to_be(target_url))
            elif condition == "changes":
                wait.until(EC.url_changes(target_url))
            elif condition == "matches":
                wait.until(EC.url_matches(target_url))
            elif condition == "contains":
                wait.until(EC.url_contains(target_url))
        except TimeoutException:
            if condition != "changes":
                assert self.driver.current_url == target_url, \
                    f"{error_message}:\n{self.driver.current_url} != {target_url}"
            else:
                assert self.driver.current_url != target_url, \
                    f"{error_message}:\n{self.driver.current_url} == {target_url}"

    def wait_and_get_elements(self, element: tuple, timeout: float = 15) -> list[WebElement]:
        """
        Method to deal with waiting for all elements and finding them in the DOM.

        :param element: WebElements' locator as a `tuple`
        :param timeout: Time in seconds we want to wait when locating elements
        :return: a list of WebElements to be interacted with
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.all_of(
                    EC.visibility_of_all_elements_located(element),
                    EC.presence_of_all_elements_located(element),
                )
            )
            return self.driver.find_elements(*element)
        except (TimeoutException, NoSuchElementException,
                ElementNotVisibleException):
            error = self.get_exception()
            self.meta_raise(error)

    def wait_for_element_invisibility(self, element: tuple, timeout: float = 15) -> None:
        """
        Method to wait for an element to be invisible

        :param element: WebElement locator as a `tuple`
        :param timeout: Amount of time to wait in seconds
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(element))
        except (TimeoutException, NoSuchElementException,
                ElementNotVisibleException):
            error = self.get_exception()
            self.meta_raise(error)

    def wait_for_element_text(self, element: tuple, text: str, timeout: float = 10, not_equal: bool = False) -> None:
        """
        Method to wait for an element to change to expected text

        :param element: WebElement's locator as a `tuple`
        :param timeout: Amount of time to wait in seconds
        :param text: Expected text as `str`
        :param not_equal: Flag to wait for text to not be equal to `text`
        """
        wait = WebDriverWait(self.driver, timeout)
        try:
            if not_equal:
                wait.until_not(
                    EC.text_to_be_present_in_element(element, text))
            else:
                wait.until(
                    EC.text_to_be_present_in_element(element, text))
        except (TimeoutException, NoSuchElementException,
                ElementNotVisibleException):
            error = self.get_exception()
            self.meta_raise(error)

    def wait_for_element_attribute_content(self, element: tuple, attribute_name: str, expected_content: any,
                                           timeout: float = 10) -> None:
        """
        Wait for an expected attribute content of an element.
        I.e some elements' text won't be returned from `WebElement.text`, sometimes
        the content is inside the `value` attribute, which may take some time to load.

        :param element: WebElement's locator as a `tuple`
        :param attribute_name: Which attribute to get data from
        :param expected_content: Which value is expected, of any type
        :param timeout: Amount of time to wait in seconds
        """
        if self.get_attribute_content(element, attribute_name, timeout) != expected_content:
            time.sleep(timeout)

    def wait_for_element_to_be_selected(self, element: tuple | WebElement, timeout: float = 10) -> bool:
        """
        Wait for an element to be selected, i.e checkboxes

        :param element: Element's locator or `WebElement`
        :param timeout: Amount of time to wait in seconds
        """
        # if isinstance(element, tuple):
        #     target_element = self.wait_and_get_element(element, timeout)
        #
        # try:
        #     WebDriverWait(self.driver, timeout).until(
        #         EC.element_to_be_selected(target_element.location))
        # except (TimeoutException, NoSuchElementException,
        #         ElementNotVisibleException):
        #     error = self.get_exception()
        #     self.meta_raise(error)
        pass

    @staticmethod
    def get_exception():
        """
            Method to return sys.exc_info() exceptions
        """
        return sys.exc_info()

    @staticmethod
    def meta_raise(exc_info):
        """
            Method to raise caught exceptions with traceback
        """
        raise exc_info[0](exc_info[1]).with_traceback(exc_info[2])

    def get_attribute_content(self, element: tuple, attribute_name: str,
                              timeout: float = 10) -> str:
        """
        Method to get content of WebElement's attribute

        :param element: WebElement `tuple` to interact with
        :param attribute_name: ex: 'value', 'id',..., etc
        :param timeout: Amount of time to wait in seconds
        """
        return self.wait_and_get_element(element, timeout).get_attribute(attribute_name)

    class AttributeValueChanged:
        """
        A class for the condition of the WebDriverWait -- wait for the attribute changed
        """

        def __init__(self, locator, attribute_name, original_value):
            self.locator = locator
            self.attribute_name = attribute_name
            self.original_value = original_value

        def __call__(self, driver):
            element = driver.find_element(*self.locator)
            value = element.get_attribute(self.attribute_name)
            return value != self.original_value

    def open_a_new_tab(self, url: str = "") -> None:
        """
        Method to open a new tab for browser
        """
        self.driver.execute_script(f"window.open('{url}');")

    def close_current_tab(self) -> None:
        """
        Method to close a tab
        """
        self.driver.close()

    def switch_to_other_tab_by_index(self, index_of_tab: int) -> None:
        """
        Method to switch to the tab you want

        :param index_of_tab: the index of tab which starts from 0
        """
        self.driver.switch_to.window(self.driver.window_handles[index_of_tab])

    def switch_to_other_tab_by_window_id(self, window_id: str) -> None:
        """
        Method to switch to the tab you want

        :param window_id: input window's ID, you can get by "driver.current_window_handle"
        """
        self.driver.switch_to.window(window_id)

    def get_children_from_parent(self, parent: tuple | WebElement,
                                 timeout: float = 10) -> list[WebElement]:
        """
        Method to find all child elements from a given parent.

        :param parent: Locator tuple or WebElement of the parent to find children
                       of.
        :param timeout: Amount of time to pass to `wait_and_get_element`
        :returns: list of WebElements containing all found children
        """
        if isinstance(parent, tuple):
            parent = self.wait_and_get_element(parent, timeout)
        return parent.find_elements(By.XPATH, "child::*")

    def actions_wait_and_move_to_element(self, element: tuple | WebElement,
                                         timeout: float = 10) -> None:
        """
        Method to use ActionChains to move to an element

        :param element: Locator tuple or WebElement to interact with
        :param timeout: Amount of time to pass to `wait_and_get_element`
        """
        action = ActionChains(self.driver)
        if isinstance(element, tuple):
            element = self.wait_and_get_element(element, timeout)
        action.move_to_element(element).perform()
        action.reset_actions()

    def actions_move_by_offset_and_click(self, x: float = 1, y: float = 1):
        """
        Method to move to some point and click
        :param x: x-coordinate of the point you want to
        :param y:
        :return:
        """

        action = ActionChains(self.driver)
        action.move_by_offset(x, y).click().perform()
        action.reset_actions()

    def actions_wait_and_click_element(self, element: tuple | WebElement,
                                       timeout: float = 10,
                                       context: bool = False,
                                       hold: bool = False,
                                       double: bool = False,
                                       reset: bool = True) -> ActionChains:
        """
        Method to use ActionChains to click, right-click or click and hold an element

        :param element: Locator tuple or WebElement to interact with
        :param timeout: Amount of time to pass to `wait_and_get_element`
        :param context: Flag to determine if left-click or right-click
        :param hold: Flag to determine if we need to click and hold
        :param double: Flag to determine if double-click
        :param reset: Flag to determine if we want to reset the actions
        :returns: The action in case we need to perform other operations
        """
        action = ActionChains(self.driver)
        if isinstance(element, tuple):
            element = self.wait_and_get_element(element, timeout)
        if context:
            action.context_click(element).perform()
        elif hold:
            action.click_and_hold(element).perform()
        elif double:
            action.double_click(element).perform()
        else:
            action.click(element).perform()
        if reset:
            action.reset_actions()
        else:
            return action

    def actions_drag_and_drop_by_offset(self, element: tuple | WebElement,
                                        x: float = 0, y: float = 0,
                                        timeout: float = 10) -> None:
        """
        Method to use ActionChains to drag and drop a WebElement by x/y coords.

        :param element: Locator tuple or WebElement to interact with
        :param x: Number of pixels to move in `x` axis
        :param y: Number of pixels to move in `y` axis
        :param timeout: Amount of time to pass to `wait_and_get_element`
        """
        action = ActionChains(self.driver)
        if isinstance(element, tuple):
            element = self.wait_and_get_element(element, timeout)
        action.drag_and_drop_by_offset(element, x, y).perform()
        action.reset_actions()

    def actions_drag_and_drop(self, source: tuple | WebElement,
                              target: tuple | WebElement,
                              timeout: float = 10) -> None:
        """
        Method to use ActionChains to drag and drop a WebElement to another.

        :param source: From which element to drag
        :param target: To which element to drop
        :param timeout: Amount of time to pass to `wait_and_get_element`
        """
        action = ActionChains(self.driver)
        if isinstance(source, tuple):
            source = self.wait_and_get_element(source, timeout)
        if isinstance(target, tuple):
            target = self.wait_and_get_element(target, timeout)
        action.drag_and_drop(source, target).perform()
        action.reset_actions()

    def js_drag_and_drop(self, source: tuple | WebElement,
                         target: tuple | WebElement,
                         timeout: float = 10) -> None:
        """
        Workaround in case actions_drag_and_drop does not work in a particular page

        :param source: From which element to drag
        :param target: To which element to drop
        :param timeout: Amount of time to pass to `wait_and_get_element`
        """
        js_function = object.javascript_functions.SIMULATE_DRAG_DROP
        if isinstance(source, tuple):
            source = self.wait_and_get_element(source, timeout)
        if isinstance(target, tuple):
            target = self.wait_and_get_element(target, timeout)
        self.driver.execute_script(js_function, source, target)

    def js_scroll_into_view(self, element: tuple | WebElement,
                            timeout: float = 10) -> None:
        """
        Method to scroll to an element until it's in view using javascript.

        :param element: Locator tuple or WebElement
        :param timeout: Amount of time to pass to `wait_and_get_element`
        """
        if isinstance(element, tuple):
            element = self.wait_and_get_element(element, timeout)
        self.driver.execute_script("arguments[0].scrollIntoView();", element)

    def default_switch(self) -> None:
        """
        Method to switch back to the default frame
        """
        self.driver.switch_to.default_content()

    def iframe_switch(self, element: tuple | WebElement,
                      timeout: float = 10) -> None:
        """
        Method to switch to iframe

        :param element: Locator tuple or WebElement
        :param timeout: Amount of time to pass to `wait_and_get_element`
        """
        if isinstance(element, tuple):
            element = self.wait_and_get_element(element, timeout)
        self.driver.switch_to.frame(element)

    def wait_and_check_if_element_exist_or_visible(self, element: tuple, timeout: float = 15) -> bool:
        """
        Method to deal with waiting for all elements and return if it exist or present in DOM.

        :param element: WebElements' locator as a `tuple`
        :param timeout: Time in seconds we want to wait when locating elements
        :return: a list of WebElements to be interacted with
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.all_of(
                    EC.visibility_of_element_located(element),
                    EC.presence_of_element_located(element),
                )
            )
            return True
        except (TimeoutException, NoSuchElementException,
                ElementNotVisibleException):
            return False

    def get_tooltip_text(self, hover_element: tuple, tooltip_element: tuple) -> str:
        """
        Get the tooltip of element

        :param hover_element: the target element
        :param tooltip_element: the tooltip element
        :return: tooltip text
        """

        self.actions_wait_and_move_to_element(hover_element)
        return self.get_element_text(tooltip_element)

    def upload_img(self, input_element: tuple, filepath: str):
        """
        Find the input tag to upload the file

        :param input_element: the input tag element
        :param filepath: upload file directory
        """
        self.driver.find_element(*input_element).send_keys(os.path.abspath(filepath))

    def js_scroll_to(self, element: tuple | WebElement, timeout: float = 10, width: float = 0,
                     height: float = 0) -> None:
        """
        Method to scroll to an location

        :param element: Locator tuple or WebElement
        :param timeout: Amount of time to pass to `wait_and_get_element`
        :param width: width you want to scroll to
        :param height: height you want to scroll to
        """
        js_code = f"arguments[0].scrollTo({width},{height});"

        if isinstance(element, tuple):
            element = self.wait_and_get_element(element, timeout)

        self.driver.execute_script(js_code, element)

    def get_scroll_height(self, element: tuple | WebElement, timeout: float = 10):
        """
        Method to get scroll height

        :param element: Locator tuple or WebElement
        :param timeout: Amount of time to pass to `wait_and_get_element`
        """
        js_code = f"return arguments[0].scrollHeight;"
        if isinstance(element, tuple):
            element = self.wait_and_get_element(element, timeout)
        return self.driver.execute_script(js_code, element)

    def scroll_and_get_until_element_exist_or_visible(self, scrollable_element: tuple | WebElement, element: tuple,
                                                      timeout: float = 0.5, width: float = 0, height: float = 0,
                                                      step=100):
        """
        :param scrollable_element: locator tuple or WebElement for scroll
        :param element: locator tuple or WebElement to get
        :param timeout: timeout for check if the element exist
        :param width: origin width you want to scroll to
        :param height: origin height you want to scroll to
        :param step: distance you want to scroll
        :return:
        """
        if isinstance(scrollable_element, tuple):
            scrollable_element = self.wait_and_get_element(scrollable_element, 5)
        time.sleep(1)
        scroll_height = self.get_scroll_height(scrollable_element)
        height = 0
        print(scroll_height)
        while height < scroll_height + step:
            self.js_scroll_to(scrollable_element, height=height)
            height += step

        return self.wait_and_get_element(element)

    def scroll_to_page_top(self):
        """
        Method to scroll the page to the top
        """
        self.driver.find_element(by=By.TAG_NAME, value='body').send_keys(Keys.CONTROL + Keys.HOME)

    def select_element_in_dropdown(self, dropdown_element: tuple | WebElement, select_item: str):
        """
        Method to Select a WebElement
        :dropdown_element: locator tuple for dropdown element
        :select_item: locator tuple for select item
        """
        self.wait_and_get_element(dropdown_element)
        dropdown = Select(self.driver.find_element(*dropdown_element))
        dropdown.select_by_visible_text(select_item)
