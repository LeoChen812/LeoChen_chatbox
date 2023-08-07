import time

from selenium.webdriver.chrome.webdriver import WebDriver

from object.base_page import BasePage
from object.registration import locator as clo
from selenium.webdriver.common.keys import Keys

class ChatBotPage(BasePage):
    """
    Class to
    """
    URL = "https://www.chatbot.com/chatbot-demo/"

    def __init__(self, driver: WebDriver):
        super().__init__(driver)
        self.url = "https://www.chatbot.com/chatbot-demo/"


    def open_the_chat_bot(self):
        self.iframe_switch(clo.IFRAME)
        self.click_element(clo.CHART_BUTTON)
        time.sleep(10)

    def click_question_option(self):
        self.wait_and_get_element(clo.I_HAVE_QUESTIONS_OPTION)
        self.click_element(clo.I_HAVE_QUESTIONS_OPTION)
        time.sleep(5)

    def click_price_button(self):
        self.wait_and_get_element(clo.PRICING_BUTTON)
        self.click_element(clo.PRICING_BUTTON)
        time.sleep(5)

    def click_compare_plans(self):
        self.wait_and_get_element(clo.COMPARE_PLANS)
        self.click_element(clo.COMPARE_PLANS)
        time.sleep(5)

    def input_text(self):
        self.wait_and_get_element(clo.INPUT_BAR)
        self.set_text_field(clo.INPUT_BAR, "price")
        self.click_element(clo.SEND_ICON)
        time.sleep(5)

