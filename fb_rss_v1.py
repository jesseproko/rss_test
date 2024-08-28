from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring, ElementTree

# Open the file and read the lines into a list
with open('test_fb_urls.txt', 'r') as file:
    fb_urls = file.readlines()

# Remove any leading/trailing whitespace characters (like \n)
fb_urls = [url.strip() for url in fb_urls]

# Setup Chrome
options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

# Iterate through the list of Facebook URLs
for fb_url in fb_urls:
    print(f"Processing URL: {fb_url}")    
    
    # Lists to store URLs, post time, and post texts
    post_urls = []
    post_times = []
    post_texts = []

    try:
        # Open the Facebook page
        driver.get(fb_url)
    
        try:
            # Close the popup if present
            close_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Close']"))
            )
            close_button.click()
            print("Close button clicked.")
            
        except:
            print("No close button found, continuing...")
        
        # Get the title text
        page_title = driver.title

        print("Page Title:", page_title)

        # Scroll the page to load content
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(5)
        body.send_keys(Keys.HOME)
        print("Page scrolled.")

        # Get all post elements
        posts = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@class='x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z']"))
        )

        for i, post in enumerate(posts[:3]):  # Process up to 3 posts
            try: 
                
                try:
                    # Find the top box element
                    message_element_topbox = post.find_element(By.XPATH, ".//div[@class='x78zum5 xdt5ytf xz62fqu x16ldp7u']")

                    # Find the time posted element
                    message_element_time = message_element_topbox.find_element(By.XPATH, ".//div[starts-with(@class,'html-div')]")

                    # Find the Post URL element
                    message_element_url = message_element_time.find_element(By.XPATH, ".//a")

                    # Scroll the Post URL element into view
                    driver.execute_script("arguments[0].scrollIntoView({ block: 'center', inline: 'nearest' });", message_element_url)
                                
                    # Perform hover action to potentially trigger post URL generation
                    actions = ActionChains(driver)
                    actions.move_to_element(message_element_url).pause(5).perform()

                    # Retrieve the href attribute
                    post_url = message_element_url.get_attribute('href')
                    
                    if post_url:
                        cleaned_url = post_url.split('?')[0]
                        post_urls.append(cleaned_url)
                        print(f"URL for post {i + 1}: {cleaned_url}")
                    else:
                        urls.append(fb_url)
                        print(f"No valid href found for post {i + 1}.")
                    
                    # Find the hover div class for datetime
                    dt_hidden_element = driver.find_element(By.XPATH, "//div[@class='__fb-dark-mode']")

                    # Find the nested span class for datetime
                    time_element = dt_hidden_element.find_element(By.XPATH, ".//span")

                    # Retrieve message datetime
                    if time_element.text:
                        extracted_time = time_element.text
                        # Define the format of the extracted time string
                        # Note: \u202f represents a narrow non-breaking space, which can be ignored during parsing
                        time_format = "%A, %B %d, %Y at %I:%M\u202f%p"
                        # Parse the extracted time string into a datetime object
                        parsed_time = datetime.strptime(extracted_time, time_format)
                        # Convert to the RFC-822 format for RSS
                        pub_date = parsed_time.strftime("%a, %d %b %Y %H:%M:%S GMT")
                        post_times.append(pub_date)
                        print(f'Extracted Post Time: {pub_date}')
                    else:
                        current_time = datetime.now(timezone.utc)
                        gen_date = current_time.strftime("%a, %d %b %Y %H:%M:%S GMT")                 
                        post_times.append(gen_date)
                        print(f'Generated Post Time: {gen_date}')                

                except:
                    print(f"Error processing post {i + 1}")      

                # Find and scroll to the message element
                message_element = post.find_element(By.XPATH, ".//div[@data-ad-comet-preview='message']")
                driver.execute_script("arguments[0].scrollIntoView({ block: 'center', inline: 'nearest' });", message_element)
                print(f"Scrolled to post {i + 1}.")
            
                # Click "See more" if present to expand the post
                try:
                    see_more_button = message_element.find_element(By.XPATH, ".//div[@role='button' and @tabindex='0' and contains(text(), 'See more')]")
                    actions = ActionChains(driver)
                    actions.move_to_element(see_more_button).pause(2).click().perform()
                    print(f"Clicked 'See more' for post {i + 1}.")
                    time.sleep(2)  # Allow time for the content to expand
                except:
                    print(f"No 'See more' button for post {i + 1}.")

                # Get the updated post text
                if message_element.text:
                    post_text = message_element.text
                    post_texts.append(post_text)
                    print(f"Post {i + 1}: {post_text}\n")
                else:
                    post_text = "No post text"
                    post_texts.append(post_text)
                    print(f"Post {i + 1}: {post_text}")

            except:
                post_text = "No post text"
                post_texts.append(post_text)
                print(f"Post {i + 1}: {post_text}")

    finally:
        print('Completed scraping')
    
    # Create the root element of the RSS feed
    rss = Element('rss')
    rss.set('version', '2.0')

    # Create the channel element
    channel = SubElement(rss, 'channel')

    # Add channel metadata (title, link, description)
    title = SubElement(channel, 'title')
    title.text = f'{page_title} RSS Feed'

    link = SubElement(channel, 'link')
    link.text = fb_url

    description = SubElement(channel, 'description')
    description.text = f'This is an RSS feed of the three most recent posts at {fb_url}'

    # Iterate over the lists and create an item for each post
    for post_url, post_time, post_text in zip(post_urls, post_times, post_texts):
        item = SubElement(channel, 'item')

        item_title = SubElement(item, 'title')
        item_title.text = post_text[:30]  # Use the first 30 characters of the post text as the title

        item_link = SubElement(item, 'link')
        item_link.text = post_url

        item_description = SubElement(item, 'description')
        item_description.text = post_text

        item_pubDate = SubElement(item, 'pubDate')
        item_pubDate.text = post_time

    # Convert the XML tree to a string
    rss_xml = tostring(rss, encoding='unicode', method='xml')

    # Write the RSS XML to a file
    # Remove trailing slash if present
    fb_url = fb_url.rstrip('/')

    # Extract the account name by splitting the URL
    account_name = fb_url.split('/')[-1]
    file_name = account_name+'.xml'
    with open(file_name, 'w', encoding='utf-8') as file:
        file.write(rss_xml)

    print(f"{account_name} RSS feed generated successfully!")

#Quit driver and complete program
driver.quit()