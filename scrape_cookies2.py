from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from openai import OpenAI
import time
import random
import json
'''
import logging

# Configure logging
logging.basicConfig(
    filename='/tmp/scrape.log',  # Log file path
    level=logging.DEBUG,  # Log level
    format='%(asctime)s %(levelname)s: %(message)s'
)
'''
global progress

#3.11.9 (main, Apr  2 2024, 08:25:04) [Clang 15.0.0 (clang-1500.3.9.4)]

class Screenshot:
    def __init__(self, cookies, headless=False): #False by default for testing
        self.cookies = cookies
        #print(self.cookies)
        self.driver = self.init_driver(headless)

    def init_driver(self, headless):
        options = Options()
        #options.binary_location = '/usr/bin/chrome-headless-shell-linux64/chrome-headless-shell'
        options.add_argument("--headless")
        #options.add_argument('--no-sandbox')
        #options.add_argument('--disable-dev-shm-usage')
        ##options.add_argument("--window-size=2560,1440")
        #options.add_experimental_option("excludeSwitches", ["enable-automation"])
        #options.add_experimental_option('useAutomationExtension', False)
        #options.add_argument('--disable-blink-features=AutomationControlled')

        service = Service()
        #service = Service(executable_path='/usr/bin/chromedriver-linux64/chromedriver')

        driver = webdriver.Chrome(options=options, service=service)
        return driver
    
    def add_cookies(self):
        self.driver.add_cookie({"name": "li_at", 
                   "value": f"{self.cookies}",
                   "domain": ".www.linkedin.com"
                   })

    def login(self):
        time.sleep(2)
        self.driver.get('https://www.linkedin.com/')
        #before_cookies = self.driver.get_screenshot_as_base64()
        #logging.debug(before_cookies)
        time.sleep(random.uniform(0.3,0.7))
        #print(self.cookies)
        self.add_cookies()
        #after_cookies = self.driver.get_screenshot_as_base64()
        #logging.debug(after_cookies)
        time.sleep(random.uniform(0.8,1.5))

        #self.driver.get('https://www.google.com')
        #time.sleep(5)
        #before_cookies = self.driver.get_screenshot_as_base64()
        #logging.debug(before_cookies)
        self.driver.refresh()
        #self.driver.get('https://www.linkedin.com/')
        time.sleep(2)
        #after_cookies = self.driver.get_screenshot_as_base64()
        #logging.debug(after_cookies)
        #time.sleep(2)
        #self.driver.quit()
        #quit()
        #logging.debug('error in refresh?')
        #a_refresh = self.driver.get_screenshot_as_base64()
        #logging.debug(a_refresh)

    def capture_screenshot(self, profile_url): #now captures a screenshot of both experience and education sections
        #self.driver.execute_script("document.body.style.zoom = '0.67'")
        self.driver.get(profile_url)
        time.sleep(random.uniform(2.5, 4.5))
        #logging.debug("on a profile")
    
        try:
            education_section = self.driver.find_element(By.ID, "education")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", education_section)
            #self.driver.implicitly_wait(random.randint(5, 7))
            time.sleep(random.uniform(3, 7))
            #filepath_edu = f"{save_path}{random.randint(1,1000000)}edu.png"
            edu_b64 = self.driver.get_screenshot_as_base64()
            print('working...')
        except Exception:
            print("no education found")
            edu_b64 =-1

        try:
            experience_section = self.driver.find_element(By.ID, "experience")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", experience_section)
            #self.driver.implicitly_wait(random.randint(5, 7))
            time.sleep(random.uniform(4, 7))
            #filepath_exp = f"{save_path}{random.randint(1,1000000)}exp.png"
            exp_b64 = self.driver.get_screenshot_as_base64()
            time.sleep(random.uniform(0.5,1))
        except Exception:
            print("no experiance found")

        self.driver.execute_script("window.scrollTo(0, 0);") #back to top
        self.driver.implicitly_wait(random.randint(2, 5))

        try: #try to access mutuals
            link = self.driver.find_element(By.PARTIAL_LINK_TEXT, 'mutual connection')
            self.driver.implicitly_wait(random.randint(1, 2))
            link.click()
            self.driver.implicitly_wait(random.randint(5, 8))
            connections_b64 = self.driver.get_screenshot_as_base64()
            self.driver.implicitly_wait(random.randint(2, 5))
            self.driver.back() #go back to profile for simulating activity

            return edu_b64, exp_b64, connections_b64 #case where we can return mutuals list
        
        except Exception: #if mutuals don't exist or can't be accessed
            print("no mutual connections found")
            return edu_b64, exp_b64, -1 #image3 = -1
        
    def simulate_activity(self):
        scroll_factor = random.uniform(0.1,1) #governs how far we scroll
        scroll_delta = random.uniform(0.75, 1) #governs by how much the scoll value changes

        for i in range(random.randint(2,3)): #30-90sec loop time
            self.driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {scroll_factor});")
            time.sleep(random.uniform(5,10))
            self.driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {1-scroll_factor});")
            time.sleep(random.uniform(10,20))

            scroll_factor *= scroll_delta

    def quit(self):
        self.driver.quit()

class Parser: #handles parsing screenshots
    def __init__(self, api_key):
        self.api_key = api_key
        #openai.api_key = self.api_key

    def parse_image(self, image1, image2, image3):
        if image3 == -1: #if there are no mutual connections we only parse 2 images
            if image1 == -1:
                image1 = image2
            try:
                client = OpenAI(api_key=self.api_key)
                response = client.chat.completions.create(
                model="gpt-4o",
                response_format={ "type": "json_object" },
                messages=[
                    {
                    "role": "user",
                    "content": [
                        {
                        "type": "text",
                        "text": """Based on the two pictures (LinkedIn profile), produce valid JSON code that matches the following structure:
                                {
                                    'School(s)':'String. Lists any schools that the person attended. Add the graduation year in parentheses. If none is listed, write Unknown',
                                    'Age':'Integer. The estimated age of the person based on their education years (today is July, 2024)',
                                    'Veteran':'Boolean. True if there is any indication that the person has served in the U.S. military and False otherwise',
                                    'Mutual Connections':'String. This value will ALWAYS be set to NONE',
                                    'Notes':'String. Synthesize a short bio about the person. It should include their experience, education, estimated age, and veteran information. The goal is to provide context for the fields above. State all information as fact. No filler words or phrases.'
                                }
                                """,
                        },
                        {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image1}",
                        },
                        },
                        {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image2}",
                        },
                        },
                    ],
                    }
                ],
                max_tokens=300,
                )
                return response.choices[0].message.content
            
            except Exception as e:
                print("Error in querying OpenAI API:", str(e))
                return None
            
        else: #else there are mutual connections then we parse 3 images
            if image1 == -1:
                image1 = image2
            try:
                client = OpenAI(api_key=self.api_key)
                response = client.chat.completions.create(
                model="gpt-4o",
                response_format={ "type": "json_object" },
                messages=[
                    {
                    "role": "user",
                    "content": [
                        {
                        "type": "text",
                        "text": """Based on the three pictures (LinkedIn profile), produce valid JSON code that matches the following structure:
                                {
                                    'School(s)':'String. Lists any schools that the person attended. Add the graduation year in parentheses If none is listed, write Unknown',
                                    'Age':'Integer. The estimated age of the person based on their education years (today is July, 2024)',
                                    'Veteran':'Boolean. True if there is any indication that the person has served in the U.S. military and False otherwise',
                                    'Mutual Connections':'String. List of names of mutual connections. These will only come from the final image. The image will be a list of name(s). Above the list it will say "People", "1st", "2nd", and "3rd"',
                                    'Notes':'String. Synthesize a short bio about the person. It should include their experience, education, estimated age, and veteran information. The goal is to provide context for the fields above. State all information as fact. No filler words or phrases.'
                                }
                                """,
                        },
                        {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image1}",
                        },
                        },
                        {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image2}",
                        },
                        },
                        {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image3}",
                        },
                        },
                    ],
                    }
                ],
                max_tokens=300,
                )
                return response.choices[0].message.content
            
            except Exception as e:
                print("Error in querying OpenAI API:", str(e))
                return None
            
def process_profiles(cookies, urls, api_key):
    global progress
    progress = {}
    progress['total'] = len(urls)
    progress['current'] = 1

    agent = Screenshot(cookies=cookies)
    parser = Parser(api_key)
    results = []

    try:
        agent.login() #inital login to linkedin 
    except Exception:
        print('error with cookies')
        return None
       
    for i, url in enumerate(urls):
        progress['current'] = i+1

        try:
            image1, image2, image3 = agent.capture_screenshot(url)
        except Exception:
            print("error taking screenshots")
        
        try:
            json_string = parser.parse_image(image1, image2, image3)
            json_dict = json.loads(json_string)
            json_dict['URL'] = url

            results.append(json_dict)
            #logging.debug("seems to be working, lets see: ", json_dict)

        except Exception:
            print("Insufficient data for profile number", progress['current'])
            #logging.error("No profile data for", progress["current"])
            pass

        if i+1 != len(urls): #sim activity unless final profile 
            agent.simulate_activity() #pause between profiles -- 30-90sec
        else:
            break 

    agent.quit()

    '''
    #make output csv (for now this block is for testing purposes)
    with open('/Users/evan/Desktop/profile_images/education_data.csv', 'w+', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['URL', 'School(s)', 'Age', 'Veteran', 'Mutual Connections', 'Notes'])
        writer.writeheader()
        writer.writerows(results)
    '''
    #print(results)
    return results # returns as list of json dicts (use for flask)

#==============MAIN================
'''
email = ""
password = ""  #need more secure handling eventually
profiles = ["https://www.linkedin.com/in/evanptaylor"]
#save_path = "/Users/evan/Desktop/profile_images/"
api_key = "" #needs security

process_profiles(email, password, profiles, api_key)
'''
#=================================


'''
NOTES:

CASE HAS MUTUALS
"""Based on the three pictures (LinkedIn profile), produce valid JSON code that matches the following structure:
{
    'School(s)':'String. Lists any schools that the person attended. Add the graduation year in parentheses',
    'Age':'Integer. The estimated age of the person based on their education years (today is July, 2024)',
    'Veteran':'Boolean. True if there is any indication that the person has served in the U.S. military and False otherwise',
    'Mutual Connections':'String. List of names of mutual connections',
    'Notes':'String. Synthesize a short bio about the person. It should include their experience, education, estimated age, and veteran information. The goal is to provide context for the fields above. State all information as fact. No filler words or phrases.'
}
""",

CASE HAS NO MUTUALS
"""Based on the two pictures (LinkedIn profile), produce valid JSON code that matches the following structure:
{
    'School(s)':'String. Lists any schools that the person attended. Add the graduation year in parentheses',
    'Age':'Integer. The estimated age of the person based on their education years (today is July, 2024)',
    'Veteran':'Boolean. True if there is any indication that the person has served in the U.S. military and False otherwise',
    'Mutual Connections':'String. This value will ALWAYS be set to NONE',
    'Notes':'String. Synthesize a short bio about the person. It should include their experience, education, estimated age, and veteran information. The goal is to provide context for the fields above. State all information as fact. No filler words or phrases.'
}
""",

"Based on the two images (a LinkedIn profile), synthesize a short bio about the person. Include education information (where and when), and an estimation of their age (today is July, 2024). If there is any indication that the person served in the U.S. military, mention it. State all information as facts. DO NOT mention when you are assuming or estimating. DO NOT include any filler words or phrases.",

'''
