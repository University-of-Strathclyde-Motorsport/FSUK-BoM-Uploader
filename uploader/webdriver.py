"""
This module implements a wrapper for the Selenium WebDriver.
"""

import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger("uploader.webdriver")


class WebDriver(webdriver.Firefox):
    """Wrapper class for Selenium WebDriver."""

    def __init__(self, timeout_time: float = 10) -> None:
        self.driver = webdriver.Firefox()
        self.timeout_time = timeout_time

    def navigate_to_page(self, url: str) -> None:
        logger.debug(f"Navigating to url '{url}'")
        self.driver.get(url)

    def wait_for_element(
        self, value: str, by: str = By.ID, clickable: bool = False
    ) -> None:
        logger.debug(f"Waiting for element '{value}'")
        if clickable:
            WebDriverWait(self.driver, self.timeout_time).until(
                EC.element_to_be_clickable((by, value))
            )
        else:
            WebDriverWait(self.driver, self.timeout_time).until(
                EC.presence_of_element_located((by, value))
            )

    def wait_for_url(self, url: str) -> None:
        WebDriverWait(self.driver, self.timeout_time).until(EC.url_matches(url))

    def get_element(self, value: str, by: str = By.ID) -> WebElement:
        element = self.driver.find_element(by, value)
        logger.debug(f"Getting element '{element}")
        return element

    def click_element(
        self, value: str, by: str = By.ID, wait_for_element: bool = True
    ) -> None:

        if wait_for_element:
            self.wait_for_element(value, by=by, clickable=True)

        element = self.driver.find_element(by, value)
        logger.debug(f"Clicking on element '{element}'")
        element.click()

    def send_keys(
        self,
        id: str,
        keystrokes: str | int | float,
        clear_element: bool = False,
        wait_for_element: bool = True,
    ) -> None:

        if wait_for_element:
            self.wait_for_element(id, clickable=True)

        element = self.get_element(id)

        if clear_element:
            element.clear()

        if keystrokes == "":
            return

        logger.debug(f"Sending keystrokes '{str(keystrokes)}' to {element}")
        element.send_keys(str(keystrokes))
