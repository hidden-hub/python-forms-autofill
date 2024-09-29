import json
import random
import time
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BROWSER_FIREFOX = "1"
BROWSER_CHROME = "2"
CONFIG_FILE_PATH = "config.json"
TEXT_FIELD_SELECTOR = "div.quantumWizTextinputPaperinputMainContent"
QUESTION_SELECTOR = "div.Qr7Oae[role='listitem']"


def pick_browser(browser_choice):
    print(f"Picking browser: {browser_choice}")
    if browser_choice == BROWSER_FIREFOX:
        return webdriver.Firefox()
    elif browser_choice == BROWSER_CHROME:
        return webdriver.Chrome()
    else:
        raise ValueError("Unsupported browser type")


def define_form_link(form_link):
    print(f"Defining form link: {form_link}")
    return form_link


def configure_driver(browser_choice):
    print("Configuring driver")
    if browser_choice == BROWSER_FIREFOX:
        firefox_options = Options()
        firefox_options.binary_location = r"C:\Program Files\Mozilla Firefox\firefox.exe"
        service = Service(executable_path="geckodriver.exe")
        driver = webdriver.Firefox(options=firefox_options, service=service)
        print("Firefox driver configured")
        return driver
    elif browser_choice == BROWSER_CHROME:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        service = Service(executable_path="chromedriver.exe")
        driver = webdriver.Chrome(options=chrome_options, service=service)
        print("Chrome driver configured")
        return driver
    else:
        raise ValueError("Unsupported browser type")


def navigate_to_form(driver, form_url):
    print(f"Navigating to form: {form_url}")
    driver.get(form_url)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, QUESTION_SELECTOR))
        )
        print("Form loaded successfully")
    except Exception as e:
        print(f"Error loading form: {e}")


def fill_text_fields(element, text="Lorem Ipsum"):
    try:
        input_field = element.find_element(By.CSS_SELECTOR, "input")
        input_field.send_keys(text)
        print("Text field filled")
    except Exception as e:
        print(f"Error filling text field: {e}")


def extract_data_params(question):
    # Attempt to extract data parameters from the question element
    try:
        data_model = question.find_element(By.CSS_SELECTOR, 'div[jsmodel="CP1oW"]')
        return data_model.get_attribute("data-params")
    except Exception as e:
        print(f"Could not find data-params: {e}")
        return None

def determine_question_type(data_params):
    # Determine the type of question based on data parameters
    question_type = "unknown"
    if data_params:
        type_match = re.search(r'null,(\d+),', data_params)
        if type_match:
            type_number = type_match.group(1)
            if type_number == "2":
                question_type = "single"
            elif type_number == "4":
                question_type = "multiple"
            elif type_number == "7":
                question_type = "grid"
            print(f"Type parameter extracted: {type_number}")
    return question_type

def determine_selection_limits(data_params):
    min_selections = None
    max_selections = None
    if data_params:
        match = re.search(r'\[\[7,\d+,\["(\d+)"\]\]', data_params)
        if match:
            min_selections = int(match.group(1))
            max_selections = int(match.group(1))
    return min_selections, max_selections

def parse_options(question, question_type):
    # Parse options based on the type of question
    options = []
    if question_type in ["single", "multiple"]:
        option_elements = question.find_elements(By.CSS_SELECTOR, "[role='radio'], [role='checkbox']")
        for opt in option_elements:
            try:
                option_text = opt.get_attribute("aria-label").strip()
                options.append((opt, option_text))
            except Exception as e:
                print(f"Error parsing option: {e}")
    elif question_type == "grid":
        row_elements = question.find_elements(By.CSS_SELECTOR, "div.EzyPc")
        for row in row_elements:
            cell_elements = row.find_elements(By.CSS_SELECTOR, "[role='checkbox'], [role='radio']")
            for cell in cell_elements:
                try:
                    option_text = cell.get_attribute("aria-label").split("Ответ: ")[1].strip(".")
                    options.append((cell, option_text))
                except Exception as e:
                    print(f"Error parsing grid option: {e}")
    return options

def extract_question_title(question):
    # Extract the title of the question
    try:
        title_element = question.find_element(By.CSS_SELECTOR, "div.HoXoMd")
        return title_element.text
    except Exception as e:
        print(f"Could not find question title: {e}")
        return "No Title"

def check_if_required(question):
    # Check if the question is marked as required
    return "Обязательный вопрос" in question.text

def parse_question(question):
    # Main function to parse the question
    print("Parsing question")
    data_params = extract_data_params(question)
    question_type = determine_question_type(data_params)
    min_selections, max_selections = determine_selection_limits(data_params)
    options = parse_options(question, question_type)
    title = extract_question_title(question)
    required = check_if_required(question)
    print(f"Final question type: {question_type}, Min: {min_selections}, Max: {max_selections}")
    return title, options, required, question_type, min_selections, max_selections


def handle_single_choice_question(options):
    if not options:
        print("No options available for single choice question")
        return
    selected_option = random.choice(options)
    option_text = selected_option[1]
    print(f"Selected option: {option_text}")
    try:
        selected_option[0].click()
        print(f"Clicked on option: {option_text}")
    except Exception as e:
        print(f"Error clicking on option '{option_text}': {e}")


def handle_multiple_choice_question(options, min_sel=1, max_sel=None):
    if not options:
        print("No options available for multiple choice question")
        return
    if min_sel and max_sel:
        if min_sel > len(options):
            max_sel = len(options)
        if max_sel > len(options):
            max_sel = len(options)
        selected_count = random.randint(min_sel, max_sel)
    elif min_sel:
        selected_count = random.randint(min_sel, len(options))
    elif max_sel:
        selected_count = random.randint(1, max_sel)
    else:
        selected_count = random.randint(1, len(options))
    selected_options = random.sample(options, selected_count)
    selected_texts = [opt[1] for opt in selected_options]
    print(f"Selected options: {selected_texts}")
    for opt in selected_options:
        option_text = opt[1]
        try:
            opt[0].click()
            print(f"Clicked on option: {option_text}")
        except Exception as e:
            print(f"Error clicking on option '{option_text}': {e}")


def handle_grid_question(options):
    if not options:
        print("No options available for grid question")
        return
    print("Handling grid question by selecting all options")
    for opt in options:
        option_text = opt[1]
        try:
            opt[0].click()
            print(f"Clicked on grid option: {option_text}")
        except Exception as e:
            print(f"Error clicking on grid option '{option_text}': {e}")


def submit_form(driver):
    try:
        submit_button = driver.find_element(By.CSS_SELECTOR, "div[role='button'][aria-label='Submit']")
        submit_button.click()
        print("Form submitted successfully")
    except Exception as e:
        print(f"Error submitting form: {e}")


def fill_form(driver):
    print("Filling form")
    question_elements = driver.find_elements(By.CSS_SELECTOR, QUESTION_SELECTOR)
    print(f"Found {len(question_elements)} questions")
    for idx, question in enumerate(question_elements, 1):
        print(f"Processing question {idx}")
        title, options, required, question_type, min_sel, max_sel = parse_question(question)
        if question_type == "single":
            handle_single_choice_question(options)
        elif question_type == "multiple":
            handle_multiple_choice_question(options, min_sel, max_sel)
        elif question_type == "grid":
            handle_grid_question(options)
    text_elements = driver.find_elements(By.CSS_SELECTOR, TEXT_FIELD_SELECTOR)
    print(f"Found {len(text_elements)} text fields to fill")
    for idx, element in enumerate(text_elements, 1):
        print(f"Filling text field {idx}")
        fill_text_fields(element)
    submit_form(driver) 


def reset_driver_to_initial_state(driver, initial_url):
    driver.delete_all_cookies()
    driver.get(initial_url) 


def load_or_request_config():
    print("Loading configuration")
    try:
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as file:
            config = json.load(file)
            print("Configuration loaded from file")
    except FileNotFoundError:
        print("Configuration file not found. Requesting input from user.")
        config = {
            "browser_choice": input("Please enter the browser choice (1 for Firefox, 2 for Chrome): "),
            "form_link": input("Please enter the form link: "),
        }
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as file:
            json.dump(config, file, ensure_ascii=False, indent=4)
            print("Configuration saved to file")
    return config


def main():
    print("Script started")
    config = load_or_request_config()
    driver = configure_driver(config["browser_choice"])
    form_url = define_form_link(config["form_link"])
    number_of_times = int(input("Enter the number of times to fill the form: ")) 

    for _ in range(number_of_times):
        navigate_to_form(driver, form_url)
        fill_form(driver)
        print("Form filled successfully")
        reset_driver_to_initial_state(driver, form_url)

    time.sleep(2)
    driver.quit()
    print("Driver quit. Script finished")


if __name__ == "__main__":
    main()