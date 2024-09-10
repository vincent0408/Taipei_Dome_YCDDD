import undetected_chromedriver as uc
import pickle

supported_websites = ['1: tixcraft', '2: famiticket']
website = input(f"Enter the number of the website that you want your cookies to be saved\n{supported_websites}: ")
if(website == '1'):
    url = 'https://tixcraft.com/'
    event_name = 'tixcraft'
elif(website == '2'):
    url = 'https://www.famiticket.com.tw/'
    event_name = 'famiticket'

driver = uc.Chrome()
driver.get(url)

# driver.set_window_position(2000, 0)
driver.maximize_window()

print('Login to your account, press any pop-ups etc.')

while(True):
    key = input("After login and finished all tasks, wait a few seconds and enter 'start' to save cookies\n")
    if(key == 'start'):
        break
pickle.dump(driver.get_cookies(), open(f"{event_name}_cookies.pkl", "wb"))
print('Cookies saved')
driver.quit()
