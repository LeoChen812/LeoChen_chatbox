"""
The test cases for test opportunities page
"""
import time
from object.registration.chat_box_object import ChatBotPage



class TestChatBoxPage:

    def test_open_pricing_page(self, init_driver):
        chat_page = ChatBotPage(init_driver)
        chat_page.go_to_link(chat_page.url)
        chat_page.open_the_chat_bot()
        chat_page.click_question_option()
        chat_page.click_price_button()
        chat_page.click_compare_plans()
        time.sleep(2)
        current_url = init_driver.current_url
        expected_url = "https://www.chatbot.com/pricing/"
        assert current_url == expected_url, f"URL mismatch! Expected: {expected_url}, Actual: {current_url}"

    def test_input_text(self, init_driver):
        chat_page = ChatBotPage(init_driver)
        chat_page.go_to_link(chat_page.url)
        chat_page.open_the_chat_bot()
        chat_page.input_text()
        chat_page.click_compare_plans()
        current_url = init_driver.current_url
        expected_url = "https://www.chatbot.com/pricing/"
        assert current_url == expected_url, f"URL mismatch! Expected: {expected_url}, Actual: {current_url}"
