import winsound
import time
import threading
import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ————— Setup Chrome —————
options = webdriver.ChromeOptions()
options.timeouts = {'script': 5000}
options.page_load_strategy = 'eager'
options.add_argument("--no-sandbox")
options.add_argument("--start-maximized")
options.add_experimental_option("excludeSwitches", ["enable-logging"])
options.add_argument("--log-level=3")
options.add_experimental_option("detach", True)

driver = webdriver.Chrome(options=options)

# ————— Load credentials —————
load_dotenv()

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
time.sleep(30)  # give the page its initial load

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

        time.sleep(20 * 60)  # every 3 minutes

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
            date_field.send_keys("072005")

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
