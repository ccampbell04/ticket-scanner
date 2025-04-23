import os
from telnetlib import EC

import resend
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless=new")  # "new" is for Chrome 109+, use "--headless" otherwise
options.add_argument("--disable-gpu")   # Optional: helps with some rendering issues


load_dotenv()

resend.api_key = os.getenv("API_KEY")
ajax_url = "https://resale.ajax.nl/secured/content"
viagogo_url = "https://www.viagogo.co.uk/Sports-Tickets/Football/European-Premier-Leagues/Dutch-Premier-League/Ajax-Amsterdam-Tickets/E-153779172"
ajax_email = os.getenv("EMAIL")
ajax_password = os.getenv("PASSWORD")

def poll_ajax():
    driver = webdriver.Chrome(options=options)
    driver.get(ajax_url)

    wait = WebDriverWait(driver, 15)  # wait up to 15 seconds

    time.sleep(2)
    driver.find_element(By.XPATH, "//input[@id='password']").send_keys(ajax_password)
    wait.until(EC.presence_of_element_located((By.ID, "signInName"))).send_keys(ajax_email)
    # press enter
    driver.find_element(By.XPATH, "//button[@id='next']").click()
    time.sleep(5)
    h3_elements = driver.find_elements(By.TAG_NAME, "h3")

    for h3 in h3_elements:
        if "Twente" in h3.text:
            try:
                # Get the following sibling div (i.e. ActionButtonContainer)
                action_container = h3.find_element(By.XPATH,
                                                   "./following-sibling::div[contains(@class, 'ActionButtonContainer')]")

                # Find the span inside that container
                span = action_container.find_element(By.XPATH, ".//span")
                span_text = span.text.strip().lower()

                if "sold out" in span_text:
                    print("❌ Found: Ajax vs Twente — SOLD OUT")
                    driver.close()
                    return False
                elif "view availability" in span_text:
                    print("✅ Found: Ajax vs Twente — BUY available")
                    driver.close()
                    return True
                else:
                    print("⚠️ Found: Ajax vs Twente — No Buy/Sold Out info found")
                    return False
            except Exception as e:
                print(f"❌ Error finding span: {e}")
    driver.close()
    driver.quit()
    return False

def poll_viagogo_2seat():
    driver = webdriver.Safari()
    driver.get(viagogo_url)

    driver.find_element(By.XPATH, "//p[text()='Allow All']/ancestor::button").click()

    driver.find_element(By.XPATH, "//button[contains(text(), 'Continue')]").click()

    sort_button_xpath = "//div[@id='stubhub-event-detail-listings-sort-dropdown']"
    driver.find_element(By.XPATH, sort_button_xpath).click()

    li_price_xpath = "//ul[@id='stubhub-event-detail-sort-dropdown-options']//li[normalize-space(text())='Price']"
    driver.find_element(By.XPATH, li_price_xpath).click()

    price_xpath = "//div[@id='listings-container']//div[@data-index='0']"
    element = driver.find_element(By.XPATH, price_xpath)
    price = element.get_attribute("data-price")

    twoSeaterPrice = price
    driver.close()

    return twoSeaterPrice

def poll_viagogo_1seat():
    driver = webdriver.Safari()
    driver.get(viagogo_url+"?quantity=1")

    driver.find_element(By.XPATH, "//p[text()='Allow All']/ancestor::button").click()

    sort_button_xpath = "//div[@id='stubhub-event-detail-listings-sort-dropdown']"
    driver.find_element(By.XPATH, sort_button_xpath).click()

    li_price_xpath = "//ul[@id='stubhub-event-detail-sort-dropdown-options']//li[normalize-space(text())='Price']"
    driver.find_element(By.XPATH, li_price_xpath).click()

    price_xpath = "//div[@id='listings-container']//div[@data-index='0']"
    element = driver.find_element(By.XPATH, price_xpath)
    price = element.get_attribute("data-price")

    oneSeatPrice = price
    driver.close()

    return oneSeatPrice

def email(subject, content):
    params: resend.Emails.SendParams = {
        "from": "Ajax Alerts <ajax@matchdayescapes.co.uk>",
        "to": ["cjscampbell@icloud.com"],
        "subject": subject,
        "html": content,
    }

    email = resend.Emails.send(params)
    print(email)

def facilitator():
    counter = 120
    print(time.localtime().tm_hour)
    while True:
        print("counter" + str(counter))
        try:
            isAvailable = poll_ajax()
            if isAvailable:
                ajax_subject = "AJAX TICKETS AVAILABLE ❌❌❌"
                ajax_content = ajax_url
                email(ajax_subject, ajax_content)
        except Exception as e:
            print(e)

        if counter == 120:
            counter = 0
            try:
                price1 = poll_viagogo_1seat()
                price2 = poll_viagogo_2seat()
                viagogo_subject = f"VIAGOGO: 1 seat: {price1} / 2 seats: {price2}"
                viagogo_content = viagogo_url
                email(viagogo_subject, viagogo_content)
            except Exception as e:
                print(e)
        counter += 1

        time.sleep(60)
        # if after midnight CET, 8 hour break
        if time.localtime().tm_hour == 23:
            print("Sleeping for 8 hours")
            time.sleep(21600)

if __name__ == "__main__":
    facilitator()