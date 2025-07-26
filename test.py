# from hunt2 import scrape_tag_details_from_page

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
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import random
# add url to to bs4
with open("./html_with_tag.html", "r", encoding="utf-8") as file:
    html_content = file.read()
soup = BeautifulSoup(html_content, 'html.parser')
# print(soup)

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

def store_processed_tag(tag_name, unit, hunt_type, dates, tag_imag):
    today = datetime.now().strftime("%Y-%m-%d")
    toda_time = datetime.now().strftime("%H:%M")
    # if you don’t yet have a header row, you can write one yourself:
    if not os.path.exists("processed_tags.csv"):
        with open("processed_tags.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["tag_name","unit","type","dates","date_recorded"])
    # now append the new line
    with open("processed_tags.csv", "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([tag_name, unit, hunt_type, dates, today, toda_time, tag_img])

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
    dates      = parts[2] if len(parts)>2 else ""
    return unit, hunt_type, dates
def get_random_interval(min_seconds=60, max_seconds=14*60):
    """
    Return a random number of seconds corresponding to
    a random integer minute value between min_minutes and max_minutes.
    """
    seonds = random.randint(min_seconds, max_seconds)
    return seonds
def keep_alive():
    while True:
        
        interval = get_random_interval(60, 14*60)
        print(f"[keep_alive] sleeping for {interval} seconds")
        time.sleep(interval)

threading.Thread(target=keep_alive, daemon=True).start()

grids = soup.find_all('mat-card', class_='mat-card')


# print(grids)
for grid in grids:
    tag_name, tag_description, tag_img= scrape_tag_details_from_page(grid)
    print(parse_tag_description(tag_description))
    unit, hunt_type, dates = parse_tag_description(tag_description)
    # 
    if not is_tag_processed(tag_name, unit, hunt_type, dates):
        store_processed_tag(tag_name, unit, hunt_type, dates, tag_img)
        print(is_tag_processed(tag_name, unit, hunt_type, dates))
    # if tag_name and tag_description:
        # print(f"Tag Name: {tag_name}, Description: {tag_description}")