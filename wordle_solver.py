from google import genai
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import time

load_dotenv()
API_KEY = os.getenv('API_KEY')

class WordleSolver:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start_browser(self):
        """Initialize browser and navigate to Wordle (Runs only once)"""
        self.playwright = sync_playwright().start()
        
        # Launch with stealth settings
        self.browser = self.playwright.chromium.launch(
            headless=False, 
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--start-maximized'
            ]
        )

        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            java_script_enabled=True,
            bypass_csp=True
        )

        # Add stealth script
        self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

        self.page = self.context.new_page()
        
        # Navigate to Wordle
        print("Navigating to Wordle...")
        self.page.goto("https://www.nytimes.com/games/wordle/index.html", wait_until="domcontentloaded")
        time.sleep(1)
        
        # Handle Popups
        self.page.get_by_text("Play").click()
        time.sleep(1)
        self.page.get_by_label("Close").click()
        time.sleep(1)

    def submit_guess(self, word, attempt):
        """Inputs the guess into the page"""
        print(f"--- Attempt {attempt}: Trying word '{word}' ---")
        
        self.page.keyboard.type(word)
        self.page.keyboard.press("Enter")
        time.sleep(3) # Wait for animation

        tiles = ["N/A"] * 5
        status_text = ""
        
        # Scrape colors
        for x in range(1, 6):
            row_locator = self.page.get_by_label(f"Row {attempt}")
            tile_locator = row_locator.get_by_label(f"{x}")
            
            background_color = tile_locator.evaluate("""(element) => {
                return window.getComputedStyle(element).getPropertyValue('background-color');
            }""")

            color_name = "Grey" # Default
            if background_color == "rgb(120, 124, 126)": color_name = "Grey"
            elif background_color == "rgb(201, 180, 88)": color_name = "Yellow"
            elif background_color == "rgb(106, 170, 100)": color_name = "Green"
            
            tiles[x-1] = color_name
            status_text += f"Letter {x} ({word[x-1]}): {color_name}\n"

        # Check Win Condition
        if all(t == "Green" for t in tiles):
            return "SOLVED"
        
        return status_text

    def close(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

if __name__ == "__main__":
    client = genai.Client(api_key=API_KEY)
    chat = client.chats.create(model="gemini-3-flash-preview")

    solver = WordleSolver()
    solver.start_browser()

    counter = 0
    message = "I am attempting today's wordle. Give me a 5 letter word to start. Put the word between underbars (_). Example: _APPLE_"

    try:
        while counter < 6:
            print(message)
            res = chat.send_message(message).text
            print(res)
            
            try:
                start_index = res.index("_") + 1
                end_index = res.index("_", start_index)
                next_word = res[start_index:end_index]
            except ValueError:
                print("Could not find word in underbars. Retrying...")
                message = "Please format the word strictly between underbars like _HELLO_."
                continue

            result_status = solver.submit_guess(next_word, counter + 1)
            
            if result_status == "SOLVED":
                print(f"Wordle Solved in {counter + 1} attempts!")
                break
            
            message = f"Here is the result for '{next_word}':\n{result_status}\nWhat word should I try next? Put it in underbars (_)."
            counter += 1

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Keep browser open for a few seconds to see result, then close
        time.sleep(5)
        solver.close()
