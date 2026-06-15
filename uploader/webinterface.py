"""
This module defines an interface for uploading to the FSUK website.
"""

import logging
from time import sleep

from selenium.webdriver.common.by import By

from .data import RowData
from .webdriver import WebDriver

logger = logging.getLogger("uploader.webinterface")

# URLs
LOGIN_PAGE_URL = "https://teams.formulastudent.com/Account/LogIn"
WELCOME_PAGE_URL = "https://teams.formulastudent.com/Account/Welcome"
BOM_LIST_URL = "https://teams.formulastudent.com/BOM/BOMList"
TIMEOUT_LOGIN_URL = "https://teams.formulastudent.com/Account/LogIn.aspx"

# Login page
USERNAME_FIELD = "ctl00_ContentPlaceHolder1_tbUsername"
PASSWORD_FIELD = "ctl00_ContentPlaceHolder1_tbPwd1"
SUBMIT_CREDENTIALS_BUTTON = "ctl00_ContentPlaceHolder1_btnSubmit"

# BoM list
BOM_LIST_TABLE = "bomListTable"
NEW_SNAPSHOT_BUTTON_SELECTOR = "input[value='Snapshot']"
SNAPSHOT_LABEL_FIELD = "ctl00_ContentPlaceHolder1_labelTextBox"
MAKE_SNAPSHOT_BUTTON = "ctl00_ContentPlaceHolder1_makeSnapshotButton"
EDIT_BOM_BUTTON_XPATH = ".//a[contains(text(), 'Edit')]"

# BoM editor
CHANGE_PAGE_SIZE_FIELD = "ctl00_cp_g_ctl00_ctl02_ctl00_ChangePageSizeTextBox"
CHANGE_PAGE_SIZE_BUTTON = (
    "ctl00_cp_g_ctl00_ctl02_ctl00_ChangePageSizeLinkButton"
)
REFRESH_BUTTON = "ctl00_cp_refreshButton"
NEW_PART_BUTTON = "newPartButton"
NEW_ACTION_BUTTON = "newActionButton"


def PART_NAME_LABEL_XPATH(part_name: str):
    return f"//span[contains(@id, '_partNameLabel') and text()='{part_name}']"


NEXT_PAGE_XPATH = "//input[@title='Next Page']"
FIRST_PAGE_XPATH = "//input[@title='First Page']"
CURRENT_PAGE = "ctl00_cp_g_ctl00_ctl02_ctl00_GoToPageTextBox"
PAGE_COUNT_LABEL = "ctl00_cp_g_ctl00_ctl02_ctl00_PageOfLabel"
WELCOME_TEXT = "ctl00_ltwelcome"

# Part editor modal
SYSTEM_DROPDOWN = "ctl00_cp_systemDropDown"
ASSEMBLY_DROPDOWN = "assemblyDropDown"
PART_NAME_FIELD = "ctl00_cp_partName"
QUANTITY_FIELD = "ctl00_cp_qtyTextBox"
COMMENT_FIELD = "ctl00_cp_partComments"
MAKE_RADIO_BUTTON = "ctl00_cp_mbOptions_0"
BUY_RADIO_BUTTON = "ctl00_cp_mbOptions_1"
COST_FIELD = "ctl00_cp_CostTextBox"
COST_COMMENT_FIELD = "ctl00_cp_CostCommentsTextBox"
SAVE_PART_BUTTON = "ctl00_cp_savePartButton"

# Action editor modal
ACTION_TYPE_DROPDOWN = "ctl00_cp_partTypeDropDown"
ACTION_SUBTYPE_FIELD = "ctl00_cp_subTypeTextBox"
ACTION_QUANTITY_FIELD = "ctl00_cp_actionQty"
ACTION_COMMENT_FIELD = "ctl00_cp_actionComments"
ACTION_COST_FIELD = "ctl00_cp_actionCostTextBox"
ACTION_COST_COMMENT_FIELD = "ctl00_cp_actionCostComments"
ACTION_CARBON_FOOTPRINT_FIELD = "ctl00_cp_CarbonFootprintTextBox"
ACTION_CARBON_COMMENT_FIELD = "ctl00_cp_CarbonCommentsTextBox"
SAVE_ACTION_BUTTON = "ctl00_cp_saveActionButton"


class WebInterfaceError(Exception):
    """Base class for errors raised by the web interface."""

    pass


class InvalidCredentialsError(WebInterfaceError):
    """Raised if FSUK credentials are invalid."""

    def __str__(self) -> str:
        return "Unable to log into FSUK website; invalid credentials."


class WebInterface(WebDriver):
    def log_in_to_account(self, username: str, password: str) -> None:

        logger.info("Attempting login")
        self.navigate_to_page(LOGIN_PAGE_URL)
        self.wait_for_element(USERNAME_FIELD)

        self.send_keys(USERNAME_FIELD, username)
        self.send_keys(PASSWORD_FIELD, password)
        self.click_element(SUBMIT_CREDENTIALS_BUTTON)

        try:
            self.wait_for_url(WELCOME_PAGE_URL)
            logger.info("Login successful")
        except Exception:
            if self.current_url != WELCOME_PAGE_URL:
                self.quit()
                raise InvalidCredentialsError

    def create_snapshot(self, base_revision: int, label: str) -> None:
        logger.info(
            f"Creating snapshot '{label}', base revision = {base_revision}"
        )
        self.navigate_to_page(BOM_LIST_URL)
        self.wait_for_element(BOM_LIST_TABLE)

        table = self.get_element(BOM_LIST_TABLE)
        rows = table.find_elements(By.TAG_NAME, "tr")

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")

            if len(cells) <= 2:
                continue

            revision = cells[2].text.strip()
            if int(revision) != base_revision:
                continue

            snapshot_button = row.find_element(
                By.CSS_SELECTOR, NEW_SNAPSHOT_BUTTON_SELECTOR
            )
            snapshot_button.click()
            break

        self.send_keys(SNAPSHOT_LABEL_FIELD, label)
        self.click_element(MAKE_SNAPSHOT_BUTTON)

        # Navigate to a different page and back again to refresh the table
        logger.debug("Refreshing page...")
        self.navigate_to_page(WELCOME_PAGE_URL)
        self.wait_for_url(WELCOME_PAGE_URL)
        self.navigate_to_page(BOM_LIST_URL)
        self.wait_for_element(BOM_LIST_TABLE)

        bom_list_table = self.get_element(BOM_LIST_TABLE)
        bom_list_table.find_element(By.XPATH, EDIT_BOM_BUTTON_XPATH).click()

    def upload_part(
        self,
        data: RowData,
        system: str,
        assembly: str,
        upload_cost: bool = True,
    ) -> None:

        # Refresh the page
        self.click_element(REFRESH_BUTTON)

        # Create a new part
        self.wait_for_element(NEW_PART_BUTTON, clickable=True)
        sleep(0.5)
        self.click_element(NEW_PART_BUTTON)
        self.wait_for_element(SAVE_PART_BUTTON)  # Wait for the modal to appear

        # Enter information
        self.send_keys(SYSTEM_DROPDOWN, system)
        self.send_keys(ASSEMBLY_DROPDOWN, assembly)
        self.send_keys(PART_NAME_FIELD, data.part)
        self.send_keys(QUANTITY_FIELD, data.quantity, clear_element=True)
        self.send_keys(COMMENT_FIELD, data.comment)
        if data.make_or_buy == "Make":
            self.click_element(MAKE_RADIO_BUTTON)
        else:
            self.click_element(BUY_RADIO_BUTTON)
            if upload_cost:
                self.send_keys(COST_FIELD, data.cost)
                self.send_keys(COST_COMMENT_FIELD, data.cost_comment)

        # Save part
        self.click_element(SAVE_PART_BUTTON)
        self.wait_for_element(REFRESH_BUTTON, clickable=True)

    def select_part(self, part: str) -> bool:

        while True:
            # Wait for page to load
            self.wait_for_element(REFRESH_BUTTON, clickable=True)
            try:
                # Search for the part in the table
                xpath = PART_NAME_LABEL_XPATH(part)
                part_row = self.get_element(xpath, by=By.XPATH)

                # Click elsewhere to ensure the row is deselected
                self.click_element(WELCOME_TEXT)

                # Now click the row to select it
                part_row.click()
                return True

            except Exception:
                # If the part is not found, move to the next page
                current_page = self.get_element(CURRENT_PAGE).get_attribute(
                    "value"
                )
                page_count_label = self.get_element(
                    PAGE_COUNT_LABEL
                ).get_attribute("innerHTML")
                max_page = (
                    page_count_label.replace("of ", "")
                    if page_count_label is not None
                    else "?"
                )
                if current_page == max_page:
                    print(
                        f"Current page: {current_page} / Max page: {max_page}"
                    )
                    self.click_element(FIRST_PAGE_XPATH, by=By.XPATH)
                else:
                    self.click_element(NEXT_PAGE_XPATH, by=By.XPATH)

    def upload_step(self, data: RowData, upload_cost: bool = True) -> None:

        # Create a new action
        self.click_element(NEW_ACTION_BUTTON)
        self.wait_for_element(
            SAVE_ACTION_BUTTON
        )  # Wait for the modal to appear

        # Enter information
        self.send_keys(ACTION_TYPE_DROPDOWN, data.step_type)
        self.send_keys(ACTION_SUBTYPE_FIELD, data.subtype)
        self.send_keys(ACTION_QUANTITY_FIELD, data.quantity, clear_element=True)
        self.send_keys(ACTION_COMMENT_FIELD, data.comment)
        if upload_cost:
            self.send_keys(ACTION_COST_FIELD, data.cost)
            self.send_keys(ACTION_COST_COMMENT_FIELD, data.cost_comment)
            self.send_keys(ACTION_CARBON_FOOTPRINT_FIELD, data.carbon_footprint)
            self.send_keys(ACTION_CARBON_COMMENT_FIELD, data.carbon_comment)

        # Save action
        sleep(0.5)
        self.click_element(SAVE_ACTION_BUTTON)
        sleep(0.5)
        self.wait_for_element(REFRESH_BUTTON, clickable=True)
