import winsound
import time
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver
import smtplib
from email.message import EmailMessage
from selenium.webdriver.support import expected_conditions as EC
import os
from dotenv import load_dotenv
import threading

options = webdriver.ChromeOptions()
options.timeouts = { 'script': 5000 }
options.page_load_strategy = 'eager'
options.add_argument("--no-sandbox")
options.add_argument("--start-maximized")
options.add_experimental_option("excludeSwitches", ["enable-logging"])
options.add_argument("--log-level=3")
options.add_experimental_option("detach", True)

driver = webdriver.Chrome(options=options)

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



driver.get('https://nevada.licensing.app')

time.sleep(60)

no_tags_msg = (
    "There are currently no First Come, First Serve tags available."
)

# — loop & refresh logic —
REFRESH_INTERVAL = 1 * 60     # 5 minutes
POST_REFRESH_WAIT = 30        # seconds after each load

if send_email(
            subject="🏷️ Starting to run a script to get a Tags",
            body=(
                "Starting a Script to look for the tags. "
                "After recieving Confirmation email Head over to https://nevada.licensing.app"
                " to add to cart!"
            )
        ):
    print("Notification email delivered.")
else:
    print("You may want to retry or check your SMTP settings.")

def keep_alive():
    """
    Every 4 minutes, do a HEAD against your app’s origin
    so the session cookie stays fresh.
    """
    while True:
        try:
            # you can also point this at a known API endpoint if you have one:
            driver.execute_script(
                "fetch(window.location.origin, { method: 'HEAD', credentials: 'same-origin' })"
                ".catch(()=>{});"
            )
        except Exception:
            pass
        time.sleep(240)  # 4 minutes

# start it as a daemon so it won’t block exit
threading.Thread(target=keep_alive, daemon=True).start()

while True:
    try:

        check_input = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(
            (By.CLASS_NAME, "mat-radio-inner-circle")
        )
    )
        check_input.click()

        is_checked = check_input.is_selected()
        assert is_checked == False

 
        date_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "residencyDate"))
        )
        date_field.clear()
        date_field.send_keys("072005")  # your MMDDYY or whatever format

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
        if send_email(
            subject="🏷️ Nevada Tag Available!",
            body=(
                "Good news — the FCFS page just showed you are eligible. "
                "Head over to https://nevada.licensing.app"
                " to add to cart!"
            )
        ):
            print("Notification email delivered.")
        else:
            print("You may want to retry or check your SMTP settings.")

        driver.quit()

    except TimeoutException:
        print(f"[{time.strftime('%X')}] Still not ELIGIBLE…")

    driver.refresh()

