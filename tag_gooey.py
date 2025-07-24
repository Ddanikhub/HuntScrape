import threading
import time
import winsound
import smtplib
import argparse
from email.message import EmailMessage
from gooey import Gooey, GooeyParser
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def start_watcher(config):
    """
    Runs the tag-watch logic using config dict and prints log messages to console
    """
    def log(msg):
        print(msg)

    # Unpack config
    SMTP_HOST = config.smtp_host
    SMTP_PORT = config.smtp_port
    SMTP_USER = config.smtp_user
    SMTP_PASS = config.smtp_pass
    SMTP_TO   = [addr.strip() for addr in config.smtp_to.split(',') if addr.strip()]
    USER_EMAIL = config.ndow_email
    USER_PASS  = config.ndow_pass
    RESIDENCY_DATE = config.residency_date

    def send_email(subject, body):
        msg = EmailMessage()
        msg['From'] = SMTP_USER
        msg['To'] = ','.join(SMTP_TO)
        msg['Subject'] = subject
        msg.set_content(body)
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(SMTP_USER, SMTP_PASS)
                smtp.send_message(msg)
            log(f"✅ Email sent: {subject}")
            return True
        except Exception as e:
            log(f"❌ Email failed: {e}")
            return False

    # Chrome setup
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--start-maximized")
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-password-manager"])
    prefs = {
        "safebrowsing.enabled": True,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.password_leak_detection_enabled": False,
        "profile.password_manager_leak_detection": False
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument(
        "--disable-features=PasswordLeakDetection,PasswordManagerOnboarding,PasswordManagerService"
    )
    options.add_argument("--disable-blink-features=PasswordLeakDetection")
    options.add_experimental_option("detach", True)

    log("🌐 Launching Chrome and navigating to NDOW")
    driver = webdriver.Chrome(options=options)
    driver.get('https://nevada.licensing.app')
    time.sleep(5)

    def log_in():
        log("🔑 Logging in…")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Log In']"))
        ).click()
        time.sleep(5)
        # Email
        e = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "user-email"))
        )
        e.clear(); e.send_keys(USER_EMAIL)
        # Password
        p = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "user-password"))
        )
        p.clear(); p.send_keys(USER_PASS)
        # Submit
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "login-submit"))
        ).click()
        time.sleep(5)
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "First Come, First Served Tags"))
        ).click()
        log("✅ Logged in and navigated to FCFS page")

    log_in()

    # Heartbeat to prevent idle logout and dismiss modal
    def keep_alive():
        while True:
            try:
                driver.execute_script(
                    "document.dispatchEvent(new Event('mousemove'));document.dispatchEvent(new Event('keydown'));"
                )
                btns = driver.find_elements(By.XPATH,
                    "//timeout-modal//button[normalize-space()='Continue']"
                )
                if btns:
                    btns[0].click()
                    log("🛡 Dismissed idle modal")
            except Exception:
                pass
            time.sleep(14 * 60)

    threading.Thread(target=keep_alive, daemon=True).start()

    send_email(
        subject="🏷️ Tag Watcher Started",
        body="FCFS watcher is now running."
    )

    # Monitoring loop
    POST_REFRESH_WAIT = 30
    while True:
        # re-login if needed
        if driver.find_elements(By.XPATH, "//button[normalize-space()='Log In']"):
            log_in()
        # form present?
        if driver.find_elements(By.CSS_SELECTOR, "residency-form > div.container"):
            r = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "mat-radio-inner-circle"))
            )
            r.click()
            d = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.NAME, "residencyDate"))
            )
            d.clear(); d.send_keys(RESIDENCY_DATE)
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Submit']"))
            ).click()
            log(f"⏳ Submitted form with date {RESIDENCY_DATE}")
        try:
            WebDriverWait(driver, POST_REFRESH_WAIT).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "p.eligible"))
            )
            log(f"🎉 ELIGIBLE detected at {time.strftime('%X')}")
            winsound.MessageBeep()
            send_email(
                subject="🏷️ Nevada Tag Available!",
                body="Your FCFS page shows ELIGIBLE. Go add to cart!"
            )
            break
        except TimeoutException:
            log(f"Still not ELIGIBLE—retrying… {time.strftime('%X')}")
            time.sleep(5)


@Gooey(program_name="NDOW FCFS Tag Watcher", advanced=True)
def main():
    parser = GooeyParser(description="Watch for Nevada FCFS tags")
    parser.add_argument(
        '--residency_date',
        metavar='Residency Date (MMDDYY)',
        widget='TextField',
        required=True
    )
    parser.add_argument(
        '--smtp_host',
        metavar='SMTP Host',
        default='smtp.gmail.com'
    )
    parser.add_argument(
        '--smtp_port',
        metavar='SMTP Port',
        type=int,
        default=587
    )
    parser.add_argument(
        '--smtp_user',
        metavar='SMTP Username',
        required=True
    )
    parser.add_argument(
        '--smtp_pass',
        metavar='SMTP Password',
        widget='PasswordField',
        required=True
    )
    parser.add_argument(
        '--smtp_to',
        metavar='Email Recipients (comma-separated)',
        required=True
    )
    parser.add_argument(
        '--ndow_email',
        metavar='NDOW Login Email',
        required=True
    )
    parser.add_argument(
        '--ndow_pass',
        metavar='NDOW Password',
        widget='PasswordField',
        required=True
    )

    args = parser.parse_args()
    start_watcher(args)

if __name__ == '__main__':
    main()
