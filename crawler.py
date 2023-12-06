import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import cv2
import numpy as np
import ddddocr
import pickle

options = uc.ChromeOptions()
event = '23_abc30'
url = f'https://tixcraft.com/activity/detail/{event}'
driver = uc.Chrome()
driver.maximize_window()
driver.get(url)
print(driver.find_element(By.CSS_SELECTOR, "h1").text)

def wait_until(css_selector, wait=10, mode=0, all=False, element=driver):
    if(mode == 0 and not all):
        return WebDriverWait(element, wait).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
    elif(mode == 0 and all):
        return WebDriverWait(element, wait).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector)))
    elif(mode == 1 and not all):
        return WebDriverWait(element, wait).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_selector)))
    elif(mode == 1 and all):
        return WebDriverWait(element, wait).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, css_selector)))
    
def refresh_cookies():
    import time
    wait_until("button[id='onetrust-reject-all-handler']", mode=1).click()
    wait_until("a[href='#login']").click()
    wait_until("a[id='loginGoogle']", mode=1).click()
    wait_until("input[type='email']", mode=1, wait=20).send_keys(email)
    wait_until("button[jsname='LgbsSe'][data-idom-class='nCP5yc AjY5Oe DuMIQc LQeN7 qIypjc TrZEUc lw1w4b']").click()
    wait_until("input[type='password']", mode=1, wait=20).send_keys(pw)
    wait_until("button[jsname='LgbsSe'][data-idom-class='nCP5yc AjY5Oe DuMIQc LQeN7 qIypjc TrZEUc lw1w4b']").click()
    time.sleep(10)
    pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))

creds = []
with open('./credentials') as f:
    for cred in f.readlines():
        creds.append(cred.strip().split('=')[-1])
email, pw = creds
event_name = 'JAPAN - PHILIPPINES'
event_date_time = ['2023/12/06', '12:30']
section_keywords = ['B1', '108']
price = '500'
ticket_amount = 4
n = 3
buy_tickets = ['Find tickets', '立即購票']

driver.delete_all_cookies()
cookies = pickle.load(open("cookies.pkl", "rb"))
for cookie in cookies:
    driver.add_cookie(cookie)
driver.refresh()
# wait_until("button[class='close-alert']", mode=1).click()
# refresh_cookies()

buy_event = None
while True:
    try:
        wait_until("li[class='buy'] > a", wait=1).click()
    except Exception as e:
        driver.refresh()
        continue

    if(buy_event is None):
        found_match_event = False
        tr_lst = wait_until('tbody > tr', all=True, mode=1)
        for i, tr in enumerate(tr_lst):
            dt_check, event_check = False, False
            td_lst = tr.find_elements(By.CSS_SELECTOR, 'td')
            for j, td in enumerate(td_lst):
                if(j == 0):
                    print(td.text)
                    row_texts = td.text.split(' ')
                    row_texts.pop(1)
                    if(row_texts != event_date_time):
                        break
                    else:
                        dt_check = True
                elif(j == 1):
                    if(td.text != event_name):
                        break
                    else:
                        event_check = True
                if(dt_check and event_check):
                    buy_event = td_lst[-1]
                    print(buy_event.text)
                    found_match_event = True
            if(found_match_event):
                break
        if(buy_event is None):
            buy_event = tr_lst[0].find_elements(By.CSS_SELECTOR, 'td')[-1]
        if(buy_event.text not in buy_tickets):
            buy_event = None
            continue

    try:
        WebDriverWait(driver, 2).until(EC.element_to_be_clickable(buy_event)).click()
        break
    except Exception as e:
        print(e)
        pass

chosen_section = None
group_lst = wait_until("div[class='zone area-list'] > ul", all=True, mode=1)
for group in group_lst:
    section_lst = group.find_elements(By.CSS_SELECTOR, "li")
    for section in section_lst:
        found_match_section = True
        if(section_keywords is not None):
            for kw in section_keywords:
                if(section.text.find(kw) == -1):
                    found_match_section = False
                    break
        else:
            found_match_section = False
        if(found_match_section):
            chosen_section = section.find_element(By.CSS_SELECTOR, "a")
            break
    if(found_match_section):
        break
if(chosen_section is None):
    for group in group_lst:
        section_lst = group.find_elements(By.CSS_SELECTOR, "li")
        for section in section_lst:
            if(section.text.find('Available') != -1 or section.text.find('remaining') != -1):
                chosen_section = section
                break
        if(chosen_section):
            break

while(True):
    try:
        chosen_section.click()
        break
    except:
        pass

def get_captcha_result():
    with open('captcha.png', 'wb') as f:
        f.write(wait_until("img[id='TicketForm_verifyCode-image']").screenshot_as_png)
    img = cv2.imread('captcha.png', 0)
    img = cv2.erode(img, np.ones((n, n), np.uint8)) 
    img = cv2.bitwise_not(img)
    cv2.imwrite('captcha_g.png', img)
    ocr = ddddocr.DdddOcr(show_ad=False)
    with open('captcha_g.png', 'rb') as f:
        image_bytes = f.read()
    return ocr.classification(image_bytes)

while(True):
    captcha_result = get_captcha_result()

    wait_until("input[id='TicketForm_verifyCode']").send_keys(captcha_result)
    while True:
        try:
            wait_until("input[id='TicketForm_agree']").click()
            break
        except:
            continue
    while True:
        try:
            wait_until(f"option[value='{ticket_amount}']").click()
            break
        except:
            continue
    while True:
        try:
            wait_until("button[class='btn btn-primary btn-green']", mode=1).click()
            break
        except:
            pass
    try:
        WebDriverWait(driver, 10).until(EC.alert_is_present()).accept()
    except:
        break

while True:
    pass
