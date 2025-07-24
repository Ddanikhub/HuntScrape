# FCFS Tag Watcher

A Selenium‑powered Python script that logs into Nevada’s FCFS tag portal, keeps your session alive, submits the residency form, polls for availability, and sends audible + email alerts when tags go live.

---

## Table of Contents

1. [Requirements](#requirements)
2. [Setup](#setup)
3. [Usage](#usage)
4. [Configuration](#configuration)
5. [Troubleshooting](#troubleshooting)
6. [License](#license)

---

## Requirements

* Python 3.8 or newer
* Google Chrome browser
* ChromeDriver matching your Chrome version (in your `PATH`)
* `pip` for installing dependencies

---

## Setup

1. **Clone or download** the repository.
2. **(Optional) Create a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate   # on macOS/Linux
   venv\\Scripts\\activate  # on Windows
   ```
3. **Install dependencies**:

   ```bash
   pip install selenium python-dotenv
   ```
4. **Create a `.env` file** in the project root with the following content:

   ```dotenv
   # SMTP settings for email notifications
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=you@example.com
   SMTP_PASS=your-app-password
   SMTP_TO=recipient1@example.com,recipient2@example.com

   # Login credentials for NDOW site
   USER_EMAIL=your-login-email@example.com
   USER_PASS=your-login-password

   # Residency form date (MMDDYY)
   RESIDENCY_DATE=072005
   ```
5. **Add `.env` to `.gitignore`** to keep credentials out of version control.

---

## Usage

Run the script with:

```bash
python hunt2.py
```

1. A detached Chrome window opens and logs you into the NDOW portal.
2. The script sends an initial **"Tag Watcher Started"** email.
3. A background thread simulates user activity and dismisses idle modals every 14 minutes.
4. After login, it navigates to **First Come, First Served Tags**.
5. In the monitoring loop:

   * Detects and submits the residency form if present.
   * Waits up to 30 seconds for the **ELIGIBLE** badge.
   * On detection, plays a beep and sends an **"Nevada Tag Available!"** email.
6. To continue monitoring after success, remove the `break` in the script.

---

## Configuration

You can adjust the following constants in `hunt2.py`:

| Variable              | Description                                    | Default   |
| --------------------- | ---------------------------------------------- | --------- |
| `LOGIN_DELAY`         | Seconds to wait after page load before login   | `5`       |
| `KEEP_ALIVE_INTERVAL` | Seconds between heartbeat events               | `14 * 60` |
| `POST_REFRESH_WAIT`   | Seconds to wait for ELIGIBLE badge per attempt | `30`      |

---

## Troubleshooting

* **Idle modal persists**: Ensure `KEEP_ALIVE_INTERVAL` is less than the site’s idle timeout (≈25 minutes) and fake events are dispatched correctly.
* **Login fails**: Verify `USER_EMAIL` and `USER_PASS` in `.env`, and adjust `LOGIN_DELAY` if necessary.
* **Email not sent**: Check SMTP credentials, network connectivity, and inspect console logs for errors.
* **Element not found errors**: The site’s HTML may have changed—update the selectors in the script accordingly.
* **Browser/Driver mismatch**: Ensure ChromeDriver version matches your Chrome browser version.

---

## License

This project is released under the MIT License. Use at your own risk.
