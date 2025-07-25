# StudentFormBot 🧠🤖

**StudentFormBot** is a semi-automated software robot developed in Python to streamline the student data entry process into the Jubo48 portal. It reads data from a Google Sheet, fills out the online form fields using Selenium, and pauses for manual verification and photo upload — ensuring both automation and accuracy.

---

## 🔧 Features

- ✅ Automated login to the Jubo48 portal
- ✅ Reads and validates student data from Google Sheets
- ✅ Automatically fills dropdowns, text fields, and date inputs
- ✅ Supports manual photo upload step for verification
- ✅ Saves screenshots for form preview and error debugging
- ✅ Logs activity and errors to a file for audit trail

---

## 📂 Technologies Used

- Python 3.x  
- Selenium WebDriver  
- gspread + Google API  
- Pandas  
- Webdriver Manager  
- ChromeDriver  
- Logging module

---

## 🚀 How It Works

1. Authenticates with Google Sheets using a Service Account
2. Launches Chrome browser using Selenium
3. Logs in to the Jubo48 portal with given credentials
4. Iterates over student records from the sheet
5. Fills each form field with validated data
6. Pauses for manual image upload and submission
7. Proceeds to next student upon user confirmation

---

## ⚠️ Manual Step Required

After each form is filled, you must:
- Upload the student's photo
- Verify the information
- Click the **Submit** button on the webpage
- Return to the console and press `Enter` to continue

---

## 🛡️ Security Note

**IMPORTANT:**  
Do **NOT** upload your service account credentials (`.json` file) to GitHub. Make sure your `.gitignore` includes:
