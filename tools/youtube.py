from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from config import settings


def open_youtube(query: str = ""):
    if not query:
        return "No search query provided for YouTube."

    options = webdriver.ChromeOptions()

    # Optional: another Chromium-based browser such as Brave (BROWSER_BINARY in .env)
    if settings.browser_binary:
        options.binary_location = settings.browser_binary

    options.add_argument("--start-maximized")
    # options.add_argument("--headless")  # Uncomment if you want headless mode

    # Brave uses the same ChromeDriver as Chrome
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get("https://www.youtube.com")

        wait = WebDriverWait(driver, 10)

        # Handle cookie consent popup with multiple possible selectors
        try:
            # Wait a bit for the page to load
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            # Try multiple possible consent button selectors
            consent_selectors = [
                "//button[contains(text(),'Accept all')]",
                "//button[contains(text(),'I agree')]",
                "//button[contains(text(),'Accept')]",
                "//button[contains(text(),'OK')]",
                "//button[@aria-label='Accept all']",
                "//button[contains(@class, 'consent')]//span[contains(text(), 'Accept')]",
                "//div[@id='dialog']//button[contains(text(), 'Accept')]",
                "//yt-button-renderer[@id='button']//button[contains(text(), 'Accept')]",
                "[aria-label='Accept all']",
                "[data-testid='accept-button']",
                "button[jsname='b3VHJd']",  # YouTube's specific consent button
            ]

            consent_clicked = False
            for selector in consent_selectors:
                try:
                    if selector.startswith("//"):
                        consent_button = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        consent_button = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    consent_button.click()
                    print(f"Clicked consent button with selector: {selector}")
                    consent_clicked = True
                    break
                except Exception:
                    continue

            if not consent_clicked:
                print("No consent popup found or unable to click it")

        except Exception as e:
            print(f"Error handling consent popup: {e}")
            pass

        # Wait for search box and input query
        search_box = wait.until(EC.presence_of_element_located((By.NAME, "search_query")))
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)

        # Wait for results page to load and video titles to be visible
        first_video = wait.until(EC.element_to_be_clickable((By.ID, "video-title")))
        first_video.click()

        return f"Playing '{query}' on YouTube using Brave browser."
    except Exception as e:
        return f"Failed to open YouTube: {e}"
