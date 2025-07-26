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
import csv
import re
from bs4 import BeautifulSoup
from datetime import datetime
import random
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

def is_tag_processed(tag_name, hunt_unit, tag_type, hunt_dates):
    today_date = datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists("processed_tags.csv"):
        return False

    with open("processed_tags.csv", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        # skip header
        next(reader, None)
        # read the rest
        rows = list(reader)

    # if there's nothing but the header, treat it as "already processed"
    if not rows:
        return False

    # otherwise look for a matching row
    for row in rows:
        # skip any malformed lines
        if len(row) < 7:
            continue
        stored_name, stored_unit, stored_type, stored_dates, stored_date, _, _ = row
        if (stored_name   == tag_name and
            stored_unit   == hunt_unit and
            stored_type   == tag_type and
            stored_dates  == hunt_dates and
            stored_date   == today_date):
            return True

    return False

def scrape_tag_details_from_page(grid):
    # print(grid)
    tag_name = None
    tag_description = None
    tag_img = None
    try:
        # Scrape the tag name and description
        tag_img = grid.find('img')['src']
        print(tag_img)
        eligible = (
            grid.find('mat-chip', string=re.compile(r'\bELIGIBLE\b'))
        )
        if not eligible:
            return None, None
        if eligible.get_text(strip=True) == 'ELIGIBLE':
            eligible_parent = eligible.parent.parent
            tag_name = eligible_parent.find('span', class_='product-name')
            if tag_name:
                tag_name = tag_name.get_text(strip=True)
                print(tag_name)
            tag_description = eligible_parent.find('p')
            if tag_description:
                tag_description = tag_description.get_text(strip=True)
                print(tag_description)
        return tag_name, tag_description, tag_img
    except Exception as e:
        print(f"Error scraping tag details: {e}")
        return None, None

def store_processed_tag(tag_name, hunt_unit, hunt_type, hunt_dates):
    today_date = datetime.now().strftime("%Y-%m-%d")
    today_time = datetime.now().strftime("%H:%M")
    # if you don’t yet have a header row, you can write one yourself:
    if not os.path.exists("processed_tags.csv"):
        with open("processed_tags.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["tag_name","unit","type","dates","date_recorded"])
    # now append the new line
    with open("processed_tags.csv", "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([tag_name, hunt_unit, hunt_type, hunt_dates, today_date, today_time])

def parse_tag_description(raw):
    """
    Given something like:
      "Unit: 061, 062, 064, 071, 073   •   Archery   •   Aug 01, 2025 - Aug 21, 2025"
    return a tuple (unit, hunt_type, dates).
    """
    cleaned = re.sub(r'\s+', ' ', raw).strip()
    parts  = [p.strip() for p in cleaned.split('•')]
    unit       = parts[0] if len(parts)>0 else ""
    hunt_type  = parts[1] if len(parts)>1 else ""
    hunt_dates      = parts[2] if len(parts)>2 else ""
    return unit, hunt_type, hunt_dates
    
def send_email(subject: str, body: str) -> bool:
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    USER      = os.getenv("SMTP_USER")
    PASS      = os.getenv("SMTP_PASS")
    recipients = [r.strip() for r in os.getenv("SMTP_TO", "").split(",") if r.strip()]

    msg = EmailMessage()
    msg["From"]    = USER
    msg["To"]      = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(USER, PASS)
            smtp.send_message(msg, to_addrs=recipients)
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
    USER_EMAIL = os.getenv("USER_EMAIL")
    user_email.send_keys(USER_EMAIL)

    user_pass = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='current-password']"))
                )
    user_pass.click()
    user_pass.clear()
    USER_PASS = os.getenv("USER_PASS")
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
def get_random_interval(min_seconds=60, max_seconds=14*60):
    """
    Return a random number of seconds corresponding to
    a random integer minute value between min_minutes and max_minutes.
    """
    seonds = random.randint(min_seconds, max_seconds)
    return seonds
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

        # sleep for a random 1–14 minutes
        interval = get_random_interval(60, 14*60)
        print(f"[keep_alive] sleeping for {interval} seconds")
        time.sleep(interval)

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
            RESIDENCY_DATE = os.getenv("RESIDENCY_DATE")
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
            EC.visibility_of_element_located((By.XPATH, "//mat-chip[normalize-space()='ELIGIBLE']"))
        )
        print(f"[{time.strftime('%X')}] 🎉 You are now ELIGIBLE!")
        winsound.MessageBeep()
        page_source = driver.page_source
        # print(page_source)
        soup = BeautifulSoup(page_source, 'html.parser')
        grids = soup.find_all('mat-card', class_='mat-card')
        # print(grids)
        for grid in grids:
            tag_name, tag_description, tag_img= scrape_tag_details_from_page(grid)
            # print(parse_tag_description(tag_description))
            if tag_name and tag_description:
                hunt_unit, hunt_type, hunt_dates = parse_tag_description(tag_description)
                if is_tag_processed(tag_name, hunt_unit, hunt_type, hunt_dates):
                    print(f"New tag found: {tag_name} {tag_description}")
                    # Send email notification
                    send_email(
                        subject="🏷️ Nevada Tag Available!",
                        body=(
                            f"The FCFS page just showed '{tag_name}'. "
                            f"Description: {hunt_unit} • {hunt_type} • {hunt_dates}. "
                            "Head to https://nevada.licensing.app to add to cart!"
                        )
                    )
                    # Store the processed tag so it doesn't send again
                    store_processed_tag(tag_name, hunt_unit, hunt_type, hunt_dates, tag_img)
                else:
                    print(f"Tag '{tag_name}' with description '{tag_description}' has already been processed today. Skipping email.")
            else:
                print("No tag details found.")

        time.sleep(5 * 60)

    except TimeoutException:
        print(f"[{time.strftime('%X')}] Still not ELIGIBLE—retrying…")

# note: no driver.refresh() needed since keep_alive() keeps your session live
