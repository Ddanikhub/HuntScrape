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

# add url to to bs4
with open("./html_with_tag.html", "r", encoding="utf-8") as file:
    html_content = file.read()
soup = BeautifulSoup(html_content, 'html.parser')
# print(soup)

def is_tag_processed(tag_name, unit, tag_type, dates):
    today = datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists("processed_tags.csv"):
        return False

    with open("processed_tags.csv", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)  # Skip header if present
        for row in reader:
            stored_name, stored_unit, stored_type, stored_dates, stored_date = row
            if (stored_name == tag_name and
                stored_unit == unit and
                stored_type == tag_type and
                stored_dates == dates and
                stored_date == today):
                return True
    return False

def parse_tag_description(raw):
    """
    Given a raw description like:
      "Unit: 061, 062, 064, 071, 073   •   Archery   •   Aug 01, 2025 - Aug 21, 2025"
    return a dict with keys 'unit', 'type', 'dates'.
    """
    # 1) Collapse all whitespace into single spaces
    cleaned = re.sub(r'\s+', ' ', raw).strip()
    # 2) Split on bullet
    parts = [p.strip() for p in cleaned.split('•')]
    return {
        'unit': parts[0] if len(parts) > 0 else None,
        'type': parts[1] if len(parts) > 1 else None,
        'dates': parts[2] if len(parts) > 2 else None,
    }

def scrape_tag_details_from_page(grid):
    # print(grid)
    tag_name = None
    tag_description = None
    try:
        # Scrape the tag name and description
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
        return tag_name, tag_description
    except Exception as e:
        print(f"Error scraping tag details: {e}")
        return None, None

def store_processed_tag(tag_name, unit, hunt_type, dates):
    today = datetime.now().strftime("%Y-%m-%d")
    # if you don’t yet have a header row, you can write one yourself:
    if not os.path.exists("processed_tags.csv"):
        with open("processed_tags.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["tag_name","unit","type","dates","date_recorded"])
    # now append the new line
    with open("processed_tags.csv", "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([tag_name, unit, hunt_type, dates, today])

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

grids = soup.find_all('mat-card', class_='mat-card')
# print(grids)
for grid in grids:
    tag_name, tag_description = scrape_tag_details_from_page(grid)
    print(parse_tag_description(tag_description))
    unit, hunt_type, dates = parse_tag_description(tag_description)
    print(is_tag_processed(tag_name, unit, hunt_type, dates))
    store_processed_tag(tag_name, unit, hunt_type, dates)
    # if tag_name and tag_description:
        # print(f"Tag Name: {tag_name}, Description: {tag_description}")