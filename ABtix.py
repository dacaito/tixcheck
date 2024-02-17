import time
import csv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import os

# Function to read the last times from the CSV file
def read_last_times_from_csv(file_path):
	try:
		with open(file_path, mode='r') as csv_file:
			csv_reader = csv.DictReader(csv_file)
			for row in csv_reader:
				return int(row['lastMessage']), int(row['lastGeneralAdmMessage'])
	except FileNotFoundError:
		return None, None

# Function to write the current times to the CSV file
def write_current_times_to_csv(file_path, last_message_time, last_general_adm_message_time):
	with open(file_path, mode='w', newline='') as csv_file:
		fieldnames = ['lastMessage', 'lastGeneralAdmMessage']
		csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
		csv_writer.writeheader()
		csv_writer.writerow({'lastMessage': last_message_time, 'lastGeneralAdmMessage': last_general_adm_message_time})

def send_telegram_message(bot_token, chat_id, message):
    send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&parse_mode=Markdown&text={message}'
    response = requests.get(send_text)
    return response.json()

# Access the secrets from the environment
abt_password = os.getenv('ABT_PASSWORD')
abt_tel_chat_id = os.getenv('ABT_TEL_CHAT_ID')
abt_tel_token = os.getenv('ABT_TEL_TOKEN')
abt_user_name = os.getenv('ABT_USER_NAME')

chrome_options = Options()
chrome_options.add_argument('--ignore-ssl-errors=yes')
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument("--headless")
chrome_options.add_argument("--log-level=1")  # This sets the logging level to only show severe errors


driver = webdriver.Chrome(options=chrome_options)  # Optional argument, if not specified will search path.

driver.get('https://www.quicket.co.za/account/authentication/login.aspx');

# Locate the username and password fields and the submit button
username_field = driver.find_element(By.ID, 'BodyContent_BodyContent_UserName')
password_field = driver.find_element(By.ID, 'BodyContent_BodyContent_Password')
submit_button = driver.find_element(By.ID, 'BodyContent_BodyContent_LoginButton')


# Fill in the username and password
username_field.send_keys(abt_user_name)
password_field.send_keys(abt_password)
# Submit the form
submit_button.click()



driver.get('https://www.quicket.co.za/events/231484-afrikaburn-2024-creation/#/resale');
time.sleep(5) # just in case page loads slowly

ticket_types = ["General Admission", "Mayday", "New Horizon"]
available_ticket_types = []

for ticket_type in ticket_types:
	try:
		WebDriverWait(driver, 1).until(
			EC.text_to_be_present_in_element(
			(By.XPATH, f"//*[contains(text(), '{ticket_type}')]"),
			ticket_type
			)
		)
		print(f"{ticket_type} tickets available!")
		available_ticket_types.append(ticket_type)
	except:
		# This exception means the specific ticket type was not found
		print(f"No {ticket_type} tickets available.")

# Get time, and last telegram message ts
current_time = int(time.time())
last_message_time, last_general_adm_message_time = read_last_times_from_csv('msgTimes.csv')		

if available_ticket_types:
	send_message = False
	
	# Will send at most one message every 2min if it finds a general admission ticket, and every 15min if it found other tickets
	if "General Admission" in available_ticket_types and (current_time - last_general_adm_message_time) >= 120:
		send_message = True
		last_general_adm_message_time = current_time
	
	if "General Admission" not in available_ticket_types and (current_time - last_message_time) >= 900:
		send_message = True
	
	if send_message:
		ticket_list = ", ".join(available_ticket_types)
		message = f"Tickets are available: {ticket_list}\nhttps://www.quicket.co.za/events/231484-afrikaburn-2024-creation/%23/resale"
		print(message)  # Print message to console (optional)
		send_telegram_message(abt_tel_token, abt_tel_chat_id, message)
		write_current_times_to_csv('msgTimes.csv', current_time, last_general_adm_message_time)
else:
	print("No specific tickets found.")
	if current_time - last_message_time >= 3600: # more than 1h since last telegram message
		message = "Nothing found, bot still running..."
		print(message)  # Print message to console (optional)
		send_telegram_message(abt_tel_token, abt_tel_chat_id, message)
		write_current_times_to_csv('msgTimes.csv', current_time, last_general_adm_message_time)	

driver.quit
