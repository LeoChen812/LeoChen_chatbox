"""
The ChatBot element locator
"""
from selenium.webdriver.common.by import By

ALL_PAGE = (By.XPATH, "//main[@class='t-chatbot-demo']")
IFRAME = (By.XPATH, "//iframe[@id='chatbot-chat-frame']")
LOGIN_BUTTON = (By.XPATH, "//a[@data-track-category='Log In Button']")
CHAT_WINDOW = (By.XPATH, "//div[@id='app']")
CHART_BUTTON = (By.XPATH, "//div[@class='bubble']")
I_HAVE_QUESTIONS_OPTION = (By.XPATH, "//div[@data-conversation-quick-reply-title='I have questions 😊']")
PRICING_BUTTON = (By.XPATH, "//div[@data-conversation-quick-reply-title='💲 Pricing']")
COMPARE_PLANS = (By.XPATH, "//div[@data-conversation-button-tittle='💲 Compare plans']")
SEND_ICON = (By.XPATH, "//div[@class='send-icon']")
INPUT_BAR = (By.XPATH, "//div[@class='typing']/child::input")