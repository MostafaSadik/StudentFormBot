"""
Author: Mostafa Sadik
Project: StudentFormBot
Date Created: July 2025
License: Proprietary 
© 2025 Mostafa Sadik. All rights reserved.
"""
import gspread
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from oauth2client.service_account import ServiceAccountCredentials
import logging
from datetime import datetime
import time
import os


class StudentFormBot:
    def __init__(self):
        # Configuration
        self.creds_file = "student-data-upload-466707-65a065b1b378.json"
        self.sheet_name = "Student Data Upload Automation"
        self.login_url = "https://jubo48.e-laeltd.com/jubo/"
        self.add_student_url = "https://jubo48.e-laeltd.com/jubo/stu-info/student-add"
        self.dashboard_url = "https://jubo48.e-laeltd.com/jubo/stu-info/index"
        self.credentials = {
            "username": "Your User Name",
            "password": "Your Password"
        }
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        self.load_timeout = 120  # Increased timeout for slow pages
        self.element_timeout = 30  # Timeout for element interactions

    def setup_logging(self):
        """Configure logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('student_upload.log'),
                logging.StreamHandler()
            ]
        )

    def setup_driver(self):
        """Configure and return Chrome WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Set longer script and page load timeouts
        driver.set_script_timeout(self.load_timeout)
        driver.set_page_load_timeout(self.load_timeout)

        return driver

    def handle_welcome_alert(self, driver):
        """Dismiss the welcome alert if it appears"""
        try:
            alert = WebDriverWait(driver, 5).until(EC.alert_is_present())
            alert_text = alert.text
            logging.info(f"Dismissing alert: {alert_text}")
            alert.accept()
            return True
        except:
            return False

    def login(self, driver):
        """Handle login process with alert detection"""
        try:
            driver.get(self.login_url)

            # Wait for login form to be interactive
            WebDriverWait(driver, self.element_timeout).until(
                EC.element_to_be_clickable((By.NAME, "username"))
            ).send_keys(self.credentials["username"])

            driver.find_element(By.NAME, "password").send_keys(self.credentials["password"])

            # Use JavaScript click for reliability
            login_button = driver.find_element(By.TAG_NAME, "button")
            driver.execute_script("arguments[0].click();", login_button)

            # Handle welcome alert if it appears
            time.sleep(2)
            self.handle_welcome_alert(driver)

            # Verify login success
            WebDriverWait(driver, self.element_timeout).until(
                EC.url_contains("/stu-info/index")
            )
            logging.info("Login successful")
            return True

        except Exception as e:
            logging.error(f"Login failed: {str(e)}")
            driver.save_screenshot("login_failure.png")
            return False

    def wait_for_form(self, driver):
        """Wait for form to be ready"""
        try:
            WebDriverWait(driver, self.element_timeout).until(
                EC.presence_of_element_located((By.NAME, "StuName"))
            )
            logging.info("Form is ready")
            return True
        except Exception as e:
            logging.error(f"Form verification failed: {str(e)}")
            return False

    def navigate_to_form(self, driver):
        """Navigate to the student add form with direct URL"""
        try:
            driver.get(self.add_student_url)
            if self.wait_for_form(driver):
                logging.info("Directly accessed student form")
                return True
            return False
        except Exception as e:
            logging.error(f"Direct URL access failed: {str(e)}")
            return False

    def get_sheet_data(self):
        """Fetch data from Google Sheet"""
        try:
            scope = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]

            creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.creds_file,
                scope
            )
            client = gspread.authorize(creds)

            sheet = client.open(self.sheet_name)
            worksheet = sheet.sheet1
            data = worksheet.get_all_records()

            if not data:
                logging.warning("No data found in worksheet")
                return pd.DataFrame()

            df = pd.DataFrame(data)
            logging.info(f"Loaded {len(df)} records from Google Sheet")

            # Clean column names
            df.columns = [col.strip() for col in df.columns]

            # Verify critical columns
            required_columns = ['Student Name', 'Phone Number', 'Date of Birth']
            missing = [col for col in required_columns if col not in df.columns]

            if missing:
                logging.error(f"Missing required columns: {missing}")
                return pd.DataFrame()

            return df

        except Exception as e:
            logging.error(f"Failed to load sheet data: {str(e)}")
            return pd.DataFrame()

    def fill_field(self, driver, field_name, value):
        """Fill a single form field"""
        try:
            if pd.isna(value) or value == '':
                return True

            element = WebDriverWait(driver, self.element_timeout).until(
                EC.visibility_of_element_located((By.NAME, field_name))
            )
            element.clear()
            element.send_keys(str(value))
            return True
        except Exception as e:
            logging.warning(f"Could not fill {field_name}: {str(e)}")
            return False

    def select_dropdown(self, driver, field_name, value):
        """Select an option from a dropdown"""
        try:
            if pd.isna(value) or value == '':
                return True

            element = WebDriverWait(driver, self.element_timeout).until(
                EC.element_to_be_clickable((By.NAME, field_name))
            )
            Select(element).select_by_visible_text(str(value))
            return True
        except Exception as e:
            logging.warning(f"Could not select {value} in {field_name}: {str(e)}")
            return False

    def fill_form(self, driver, row):
        """Fill the student form with data"""
        try:
            # Fill dropdown fields
            self.select_dropdown(driver, 'District', row.get('District', ''))
            self.select_dropdown(driver, 'Batch', row.get('Batch', ''))
            self.select_dropdown(driver, 'Group', row.get('Your Class Group', ''))
            self.select_dropdown(driver, 'Gender', row.get('Gender', ''))
            self.select_dropdown(driver, 'Religion', row.get('Religion', ''))

            # Fill text fields
            self.fill_field(driver, 'StuName', row.get('Student Name', ''))
            self.fill_field(driver, 'FatherName', row.get('Father Name', ''))
            self.fill_field(driver, 'MotherName', row.get('Mother Name', ''))
            self.fill_field(driver, 'Age', row.get('Age', ''))
            self.fill_field(driver, 'About', row.get('About yourself/ Your Freelance Profile Description', ''))


            # Format phone number
            phone = str(row.get('Phone Number', ''))
            if phone and phone != 'nan':
                phone = ''.join(filter(str.isdigit, phone))
                if len(phone) == 10 and phone.startswith('1'):
                    phone = '0' + phone
            self.fill_field(driver, 'Contact', phone)

            self.fill_field(driver, 'Email', row.get('E-mail', ''))
            self.fill_field(driver, 'NidNo', row.get('NID/Birth Certificate No', ''))
            self.fill_field(driver, 'BloodGrp', row.get('Blood Group', ''))
            self.fill_field(driver, 'Profession', row.get('Profession', ''))
            self.fill_field(driver, 'Address', row.get('Present Address', ''))
            self.fill_field(driver, 'PermaAddress', row.get('Permanent Address', ''))
            self.fill_field(driver, 'EduQual', row.get('Last Academic Qualification', ''))
            self.fill_field(driver, 'PassYear', row.get('Passing Year', ''))

            # Handle date field
            dob_value = row.get('Date of Birth', '')
            if dob_value and str(dob_value) != 'nan':
                try:
                    dob_formatted = pd.to_datetime(dob_value).strftime('%Y-%m-%d')
                    self.fill_field(driver, 'Dob', dob_formatted)
                except:
                    logging.warning(f"Could not parse date: {dob_value}")

            # Handle radio buttons
            try:
                computer_radio = driver.find_element(By.XPATH, "//input[@name='Computer' and @value='No']")
                driver.execute_script("arguments[0].click();", computer_radio)
            except:
                pass

            return True

        except Exception as e:
            logging.error(f"Form filling error: {str(e)}")
            return False

    def process_student(self, driver, row, index, total):
        """Process a single student with manual image upload"""
        student_name = row.get('Student Name', '')
        if not student_name or pd.isna(student_name):
            return False

        logging.info(f"Processing student {index + 1}/{total}: {student_name}")

        try:
            # Navigate to form
            if not self.navigate_to_form(driver):
                logging.error("Failed to access form")
                return False

            # Fill form data
            if not self.fill_form(driver, row):
                logging.error("Form filling failed")
                return False

            # Save screenshot for reference
            driver.save_screenshot(f"form_filled_{index}.png")

            # Manual intervention step
            print("\n" + "=" * 80)
            print(f"MANUAL ACTION REQUIRED FOR: {student_name}")
            print("=" * 80)
            print("Please complete these steps in the browser:")
            print("1. Upload the student's passport-size photo")
            print("2. Verify all information is correctly filled")
            print("3. Click the 'Submit Now' button")
            print("4. After successful submission, return here")
            print("5. Press Enter to continue with the next student")
            print("=" * 80 + "\n")

            input("Press Enter AFTER submission to continue...")
            return True

        except Exception as e:
            logging.error(f"Error processing student: {str(e)}")
            driver.save_screenshot(f"error_{index}.png")
            return False

    def run(self):
        """Main execution flow"""
        self.setup_logging()
        driver = None

        try:
            driver = self.setup_driver()
            logging.info("Browser session started")

            if not self.login(driver):
                raise Exception("Login process failed")

            # Get data from Google Sheet
            data = self.get_sheet_data()
            if data.empty:
                raise Exception("No valid data to process")

            total_students = len(data)
            logging.info(f"Processing {total_students} students")

            success_count = 0
            for index, row in data.iterrows():
                # Navigate to dashboard before each student
                driver.get(self.dashboard_url)
                time.sleep(2)  # Allow page to settle

                if self.process_student(driver, row, index, total_students):
                    success_count += 1
                    logging.info(f"Completed {row['Student Name']}")

            logging.info(f"Finished processing {success_count}/{total_students} students")

        except Exception as e:
            logging.critical(f"Fatal error: {str(e)}")
        finally:
            if driver:
                try:
                    driver.get("https://jubo48.e-laeltd.com/jubo/logout")
                    logging.info("Logged out")
                except:
                    pass
                driver.quit()
            logging.info("Browser session ended")


if __name__ == "__main__":
    bot = StudentFormBot()
    bot.run()