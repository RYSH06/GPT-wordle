from playwright.sync_api import sync_playwright
import time


def scrape_wordle_status(next_word, attempt):
    """Scrape wordle and feed the status into AI to get the next best input"""
    with sync_playwright() as p:

        def wordle_guess(next_word, attempt): 
            print(f"Trying word {next_word}")
            page.keyboard.type(next_word)
            page.keyboard.press("Enter")
            time.sleep(3)
            
            tiles = ["N/A", "N/A", "N/A", "N/A", "N/A"]
            status = ""
            for x in range (1,6):
                background_color = page.get_by_label(f"Row {attempt}").get_by_label(f"{x}").evaluate("""(element) => {
                    return window.getComputedStyle(element).getPropertyValue('background-color');
                }""")
                if (background_color == "rgb(120, 124, 126)"):
                    background_color = "Grey"
                if (background_color == "rgb(201, 180, 88)"):
                    background_color = "Yellow"
                if (background_color == "rgb(106, 170, 100)"):
                    background_color = "Green"
                tiles[x - 1] = background_color
                status += f"tile{x} ({next_word[x - 1]}): {background_color}\n"

            print(status)

            return status

         # Launch with stealth settings
        browser = p.chromium.launch(
            headless=False,  # MUST be False to bypass bot detection
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--start-maximized'
            ]
        )
        
        # Create context with realistic settings
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            java_script_enabled=True,
            bypass_csp=True
        )
        
        # Add stealth script to hide automation
        context.add_init_script("""
            // Overwrite navigator.webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Overwrite chrome property
            window.chrome = {
                runtime: {}
            };
            
            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

        if attempt == 1:
            page = context.new_page()

            print("Step 1: Starting from Google...")
            page.goto("https://www.google.com", wait_until="networkidle")

            print("Step 2: Navigating to Worlde...")
            page.goto("https://www.nytimes.com/games/wordle/index.html", wait_until="domcontentloaded")
            time.sleep(0.5)

            print("Step 3: Starting daily Wordle...")
            page.get_by_text("Play").click()
            time.sleep(1)
            page.get_by_label("Close").click()
            time.sleep(1)

        status = wordle_guess(next_word, attempt)

        return status
