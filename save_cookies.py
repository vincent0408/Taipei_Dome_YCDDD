import undetected_chromedriver as uc
import pickle

supported_websites = ['tixcraft', 'famiticket']
while(True):
    website = input(f"Enter the website that you want your cookies to be saved\n{supported_websites}: ")
    if(website not in supported_websites):
        print('Not supported, please re-enter')
    else:
        break
if(website == 'famiticket'):
    url = 'https://www.famiticket.com.tw/'
elif(website == 'tixcraft'):
    url = 'https://tixcraft.com/'

driver = uc.Chrome()
driver.get(url)

# driver.set_window_position(2000, 0)
driver.maximize_window()

print('Login to your account, press any pop-ups etc.')

while(True):
    key = input("After login and finished all tasks, wait a few seconds and enter 'start' to save cookies\n")
    if(key == 'start'):
        break
pickle.dump(driver.get_cookies(), open(f"{website}_cookies.pkl", "wb"))
print('Cookies saved')
