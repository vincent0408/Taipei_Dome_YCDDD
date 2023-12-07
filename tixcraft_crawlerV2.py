import ddddocr
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pickle
from concurrent.futures import ThreadPoolExecutor
import cv2
import numpy as np
import io
from PIL import Image
import time
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--event', type=str, default='23_abc30')
parser.add_argument('--no_of_tickets', type=int, default=-1)
parser.add_argument('--start_time', type=str, default=None)   # ISO 8601: '2023-12-07T13:03:00'
parser.add_argument('--event_priority', type=list, default=[
    ['2023/12/08 (Fri.) 18:30', None, None], 
    # ['2023/12/17 (Sun.) 13:00', None, None],
    # ['2023/12/06 (Wed.) 18:30', None, None],
    # ['2023/12/09 (Sat.) 14:00', None, None],
    # ['2023/12/06 (Wed.) 18:30', None, None],    
    ])
parser.add_argument('--wanted_section_keywords_priority', type=list, default=[
    # '' for any seat will do
    ['108'], 
    ['109'],
    ['118'], 
    ['117'], 
    ['107'],
    ['119'], 
    ['113'],
    ['112'],
    ['114'],
    ['110'],  
    ['116'],
    ['111'],
    ['115'],
    [''], 
    ])
parser.add_argument('--unwanted_section_keywords', type=list, default=['外野',])
args = parser.parse_args()
url = f'https://tixcraft.com/activity/game/{args.event}'
buy_tickets_now = ['Find tickets', '立即購票']


class StartUpTasks:
    def __init__(self, driver) -> None:
        self.driver = driver
        print('Selected activity:', driver.find_element(By.CSS_SELECTOR, "h1").text)

    def adjust_window(self):
        self.driver.set_window_position(2000, 0)
        self.driver.maximize_window()
    
    def add_cookies(self):
        self.driver.delete_all_cookies()
        cookies = pickle.load(open("cookies.pkl", "rb"))
        for cookie in cookies:
            self.driver.add_cookie(cookie)

    def close_alert_button(self):
        try: 
            alert_button = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[class='close-alert']")))
            alert_button.click()
        except:
            pass

def login_tixcraft(driver):
    driver.get(url)
    start_up_tasks = StartUpTasks(driver)
    with ThreadPoolExecutor() as executor:
        executor.submit(start_up_tasks.close_alert_button)
        executor.submit(start_up_tasks.adjust_window)
        executor.submit(start_up_tasks.add_cookies)
    driver.refresh()
    return driver


def choose_event(driver):
    # -------------------choose events-------------------
    # buy_now_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "li[class='buy'] > a")))
    finished_choosing_events = False
    while(not finished_choosing_events):
        # try:
        #     buy_now_button.click()
        # except Exception as e:
        #     continue
        for event_datetime, event_name, event_venue in args.event_priority:
            print('Now trying', event_datetime, event_name, event_venue)
            matched_event_idx = None
            event_tr_lst = WebDriverWait(driver, 10).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "tbody > tr")))
            for i, event_tr in enumerate(event_tr_lst):
                event_td_lst = WebDriverWait(event_tr, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "td")))
                datetime_match, name_match, venue_match = True, True, True
                if(event_datetime is not None):
                    datetime_match = (event_td_lst[0].text == event_datetime)
                if(event_name is not None):
                    name_match = (event_td_lst[1].text == event_name)
                if(event_venue is not None):
                    venue_match = (event_td_lst[2].text == event_venue)
                if(datetime_match and name_match and venue_match):
                    matched_event_idx = i
                    matched_event_status_td = event_td_lst[-1]
                    break

            if(matched_event_idx is not None):
                current_status = matched_event_status_td.text
                if(current_status.find('Find tickets') != -1):
                    print('Found matched event', event_datetime, event_name, event_venue)
                    while(True):
                        try:
                            matched_event_status_td.click()
                            finished_choosing_events = True
                            break
                        except Exception as e:
                            continue
                elif(current_status.find('Sale starts at') != -1):
                    print(current_status, ', refreshing...', sep='')
                    time.sleep(.5)
                    driver.refresh()
                    break
                elif(current_status.find('Sale ended on') != -1):
                    continue
            else:
                print('No matched events, should abort')
                driver.refresh()
                continue
            if(finished_choosing_events):
                break

def credit_card_verification(driver, card_six='00000'):
    def enter_credit_card():
        credit_six_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='checkCode']")))
        confirm_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit']")))
        while(True):
            if(credit_six_input.get_attribute("value") != card_six):
                credit_six_input.clear()
                credit_six_input.send_keys(card_six)
            while(True):
                try:
                    confirm_button.click()
                    break
                except:
                    pass
            try:
                WebDriverWait(driver, 1).until(EC.alert_is_present()).accept()
            except:
                break
    def go_back():
        driver.back()

    if(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "li[class='active']"))).text == 'Verification'):
        go_back()
        return True
    else:
        return False



def choose_section(driver):
    # -------------------choose section-------------------
    
    if(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "li[class='active']"))).text == 'Seat Selection'):
        section_li_lst = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[class='zone area-list'] > ul > li")))
        found_matched_section = False
        while(not found_matched_section):
            for priority_keyword in args.wanted_section_keywords_priority:
                print('Searching with keywords:', *priority_keyword)
                for li in section_li_lst:
                    section_match = True
                    section_info_price = li.text
                    for wanted_kw in priority_keyword:
                        if(section_info_price.find(wanted_kw) == -1):
                            section_match = False
                            break
                    for unwanted_kw in args.unwanted_section_keywords:
                        if(section_info_price.find(unwanted_kw) != -1):
                            section_match = False
                            break
                    if(section_match and li.text.find('Sold out') == -1):                    
                        print('Found available section:', li.text)
                        while(True):
                            try:
                                li.click()
                                found_matched_section = True
                                break
                            except Exception as e:
                                continue              
                    if(found_matched_section):
                        break
                if(found_matched_section):
                    break
                print('Cannot find available sections with keywords', *priority_keyword)
        if(not found_matched_section):
            print('y')
            driver.refresh()

def enter_captcha(driver):
    def guess_captcha(driver, n=[3, 4, 2]):
        ocr = ddddocr.DdddOcr(show_ad=False)
        while(True):
            captcha = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "img[id='TicketForm_verifyCode-image']")))
            img = np.array(Image.open(io.BytesIO(captcha.screenshot_as_png)).convert('L'))
            # with open('captcha.png', 'wb') as f:
            #     f.write(captcha.screenshot_as_png)
            if(img.shape == (100, 120)):
                break
        for kernel_size in n:
            img_erode = cv2.erode(img, np.ones((kernel_size, kernel_size), np.uint8))
            # cv2.imwrite('captcha_processed.png', img_erode)
            # with open('captcha_processed.png', 'rb') as f:
            #     captcha_img = f.read()
            guess = ocr.classification(Image.fromarray(img_erode))
            if(len(guess) == 4):
                break
        if(len(guess) != 4):
            guess = ocr.classification(Image.fromarray(img))
        return guess
    try:
        captcha_guess = guess_captcha(driver)
        verify_code_box = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id='TicketForm_verifyCode']")))
        while(True):
            if(verify_code_box.get_attribute("value") != captcha_guess):
                verify_code_box.clear()
                verify_code_box.send_keys(captcha_guess)
            else:
                break
    except Exception as e:
        print(f'Enter captcha failed with {e}')

def agree_tos(driver):
    try:
        agree_tos_checkbox = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id='TicketForm_agree']")))
        while(not agree_tos_checkbox.is_selected()):
            try: 
                agree_tos_checkbox.click() 
            except: 
                continue
    except Exception as e: 
        print(f'Agree TOS failed with {e}')

def select_quantity(driver, ticket_quantity=args.no_of_tickets):
    full_ticket = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "select")))
    possible_quantity = WebDriverWait(full_ticket, 5).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "option")))
    try:
        choose_quantity = possible_quantity[ticket_quantity]
    except Exception as e:
        choose_quantity = possible_quantity[-1]
        print(f'Not enough tickets, had to go with {choose_quantity.text} tickets')
    try:
        while(not choose_quantity.is_selected()):
            choose_quantity.click()
    except Exception as e:
        print(f'Select quantity failed with {e}')

def book_tickets(driver):
    max_tries = 1000
    for _ in range(max_tries):
        with ThreadPoolExecutor() as executor:
            tasks = []
            tasks.append(executor.submit(agree_tos, driver))
            tasks.append(executor.submit(select_quantity, driver))
            tasks.append(executor.submit(enter_captcha, driver))
        submit_button = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[class='btn btn-primary btn-green']")))
        while(True):
            try:
                submit_button.click()
                break
            except:
                continue
        try:
            WebDriverWait(driver, 10).until(EC.alert_is_present()).accept()
        except:
            break

def order_summary(driver):
    if(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "li[class='active']"))).text == 'Order Summary'):
        pass

def main():
    driver = uc.Chrome()
    login_tixcraft(driver)
    # --------
    # verifying = True
    # while(verifying):
    #     choose_event(driver)
    #     verifying = credit_card_verification(driver)
    choose_event(driver)
    # --------
    choose_section(driver)
    book_tickets(driver)
    while(True):
        key = input("Enter 'quit' to quit\n")
        if(key == 'quit'):
            driver.quit()
            break


if __name__ == '__main__':
    if(args.start_time is None):
        main()
    else:
        from apscheduler.schedulers.blocking import BlockingScheduler
        import re
        start_date, hour, minute, second  = re.split('T|:', args.start_time)
        scheduler = BlockingScheduler(timezone='Asia/Taipei')
        scheduler.add_job(main, 'cron', start_date=start_date, hour=hour, minute=minute, second=second)
        scheduler.start()
