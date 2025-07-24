import winsound
import time
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver

from selenium.webdriver.support import expected_conditions as EC
# 1) Set up Chrome options to remove extra logging
options = webdriver.ChromeOptions()
options.timeouts = { 'script': 5000 }
options.page_load_strategy = 'eager'
options.add_argument("--no-sandbox")
options.add_argument("--start-maximized")
options.add_experimental_option("excludeSwitches", ["enable-logging"])
options.add_argument("--log-level=3")
options.add_experimental_option("detach", True)
# Launch the browser quietly
driver = webdriver.Chrome(options=options)




driver.get('https://nevada.licensing.app')
# print driver in json format
# wait = WebDriverWait(driver, timeout=20)
# driver.implicitly_wait(10000)
time.sleep(60)

no_tags_msg = (
    "There are currently no First Come, First Serve tags available."
)

# — loop & refresh logic —
REFRESH_INTERVAL = 1 * 60     # 5 minutes
POST_REFRESH_WAIT = 30        # seconds after each load

while True:
    try:
        # Wait up to POST_REFRESH_WAIT for the ELIGIBLE badge to appear
        

        # check_input = driver.find_element(By.CLASS_NAME, "mat-radio-inner-circle")
        check_input = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(
            (By.CLASS_NAME, "mat-radio-inner-circle")
        )
    )
        check_input.click()

        is_checked = check_input.is_selected()
        assert is_checked == False

        date_input = driver.find_element(By.NAME, "residencyDate")
        date_input.clear()  # Clear field

        insert_date = "072005"
        date_input.send_keys(insert_date)  # Enter text
        submit_btn = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[normalize-space(.)='Submit']")
        )
    )

    # Click it
        submit_btn.click()

        WebDriverWait(driver, POST_REFRESH_WAIT).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "p.eligible")
            )
        )
        print(f"[{time.strftime('%X')}] 🎉 You are now ELIGIBLE!")
        winsound.MessageBeep()   # notify you

    except TimeoutException:
        print(f"[{time.strftime('%X')}] Still not ELIGIBLE…")

    # Always sleep then refresh (keeps you logged in and checking)
    # time.sleep(REFRESH_INTERVAL)
    driver.refresh()


# …now notify or continue your workflow…
# e.g. winsound.MessageBeep() on Windows, send an email, etc.
# elem = driver.find_element(By.ID, 'login-btn')
# elem.click()
# driver.implicitly_wait(10)


# assert revealed.is_displayed() is True, "Element is not displayed"
# print("Element is displayed:", revealed.is_displayed())
# wait = WebDriverWait(driver, timeout=20)
# driver.switch_to.frame(revealed)




# # revealed.send_keys("Displayed")
# # assert revealed.get_property("value") == "Displayed"

# print("Selenium script executed successfully.")
# print("Current URL:", driver.current_url)
# print("Page title:", driver.title)
