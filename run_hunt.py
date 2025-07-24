import winsound
import time
import threading
import os
import smtplib
from email.message import EmailMessage
from selenium.common.exceptions import NoSuchElementException
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import getpass

# 1) SMTP settings
SMTP_HOST = input("SMTP host [smtp.gmail.com]: ") or "smtp.gmail.com"
SMTP_PORT = input("SMTP port [587]: ") or 587
SMTP_PORT = int(SMTP_PORT)

SMTP_USER = input("SMTP username: ")
SMTP_PASS = getpass.getpass("SMTP password (hidden): ")

to_addrs = input("Email recipients (comma-separated): ")
SMTP_TO = [addr.strip() for addr in to_addrs.split(",") if addr.strip()]

# 2) NDOW login
USER_EMAIL = input("NDOW login email: ")
USER_PASS  = getpass.getpass("NDOW password (hidden): ")

# 3) Residency date
RESIDENCY_DATE = input("Residency date (MMDDYY): ")
# ————— Setup Chrome —————
options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--start-maximized")
options.add_argument("--log-level=3")
options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-password-manager"])

# 1) Turn off the password service and leak detection prefs
prefs = {
    "safebrowsing.enabled": True,
    "credentials_enable_service": False,
    "profile.password_manager_enabled": False,
    "profile.password_leak_detection_enabled": False,
    "profile.password_manager_leak_detection": False
}
options.add_experimental_option("prefs", prefs)

# 2) Disable the feature flags
options.add_argument(
    "--disable-features="
    "PasswordLeakDetection,"
    "PasswordManagerOnboarding,"
    "PasswordManagerService"
)
options.add_argument("--disable-blink-features=PasswordLeakDetection")

# 3) Keep the browser open
options.add_experimental_option("detach", True)

driver = webdriver.Chrome(options=options)

# ————— Load credentials —————
load_dotenv()

def send_email(subject: str, body: str) -> bool:
    
    
    
    
    

    msg = EmailMessage()
    msg["From"]    = SMTP_USER 
    msg["To"]      = SMTP_TO 
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(SMTP_USER , SMTP_PASS )
            smtp.send_message(msg, to_addrs=SMTP_TO )
        print("✅ Email sent successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

# ————— Navigate once —————
driver.get('https://nevada.licensing.app')
time.sleep(5)
def log_in():

    log_in_btn = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Log In']"))
                )
    log_in_btn.click()
    time.sleep(5)
    user_email = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='username']"))
                )
    user_email.click()
    user_email.clear()
    
    user_email.send_keys(USER_EMAIL)

    user_pass = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='current-password']"))
                )
    user_pass.click()
    user_pass.clear()
    
    user_pass.send_keys(USER_PASS)

    log_in_btn_2 = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "login-submit"))
                )
    log_in_btn_2.click()
    time.sleep(5)
    nav_link = driver.find_element(By.LINK_TEXT, "First Come, First Served Tags")


    nav_link.click()

log_in()
time.sleep(5)  # give the page its initial load

# ————— Heartbeat thread —————
def keep_alive():
    while True:
        try:
            # 1) fake user events
            driver.execute_script("""
                document.dispatchEvent(new Event('mousemove'));
                document.dispatchEvent(new Event('keydown'));
            """)
            # 2) dismiss modal if it popped up
            btns = driver.find_elements(By.XPATH,
                "//timeout-modal//button[normalize-space()='Continue']"
            )
            if btns:
                btns[0].click()
        except:
            pass

        time.sleep(14 * 60)  # every 3 minutes

threading.Thread(target=keep_alive, daemon=True).start()


# ————— Initial notification —————
send_email(
    subject="🏷️ Tag Watcher Started",
    body=(
        "Your FCFS tag‑watcher script is now running. "
        "You’ll get another email once ELIGIBLE appears."
    )
)

# ————— Monitoring loop —————
POST_REFRESH_WAIT = 30  # seconds to wait per attempt

while True:

    timeout_buttons = driver.find_elements(
        By.XPATH,
        "//timeout-modal//button[normalize-space()='Continue']"
    )
    if timeout_buttons:
        timeout_buttons[0].click()

    try:
        driver.find_element(By.XPATH, "//button[normalize-space()='Log In']")
        # if we get here, the button exists → we’re logged out
        log_in()
    except NoSuchElementException:
        # button not found → we’re still logged in, do nothing
        pass

    on_form = bool(driver.find_elements(
    By.CSS_SELECTOR,
    "residency-form > div.container"
))
    if on_form:
        # 1) Click the radio button
            check_input = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.CLASS_NAME, "mat-radio-inner-circle")
            )
        )
            check_input.click()

            is_checked = check_input.is_selected()
            assert is_checked == False

            # 2) Fill the date
            date_field = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.NAME, "residencyDate"))
            )
            date_field.clear()
            
            date_field.send_keys(RESIDENCY_DATE)

            # 3) Submit
            submit_btn = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Submit']"))
            )
            submit_btn.click()
    try:
        # 4) Wait for ELIGIBLE badge
        print("Waiting form ELIGIBILITY")
        WebDriverWait(driver, POST_REFRESH_WAIT).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "p.eligible"))
        )
        print(f"[{time.strftime('%X')}] 🎉 You are now ELIGIBLE!")
        winsound.MessageBeep()

        # 5) Email alert
        if send_email(
            subject="🏷️ Nevada Tag Available!",
            body="The FCFS page just showed ‘ELIGIBLE’. Head to the site to add to cart!"
        ):
            print("Notification email delivered.")
        else:
            print("Email failed — check SMTP settings.")


    except TimeoutException:
        print(f"[{time.strftime('%X')}] Still not ELIGIBLE—retrying…")

# note: no driver.refresh() needed since keep_alive() keeps your session live
