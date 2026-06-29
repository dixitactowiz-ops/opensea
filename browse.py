from playwright.sync_api import sync_playwright

URL = "https://www.w3schools.com/python/"

NUM_BROWSERS = 3
TABS_PER_BROWSER = 3

with sync_playwright() as p:

    browsers = []

    for b in range(NUM_BROWSERS):

        browser = p.chromium.launch(
            headless=False
        )

        context = browser.new_context()

        print(f"Browser {b+1} started")

        for t in range(TABS_PER_BROWSER):

            page = context.new_page()

            try:
                page.goto(
                    URL,
                    wait_until="domcontentloaded",
                    timeout=60000
                )
                print(f"Browser {b+1} - Tab {t+1} opened")

            except Exception as e:
                print(f"Browser {b+1} - Tab {t+1} failed: {e}")

        browsers.append(browser)

    input("Press Enter to close all browsers...")

    for browser in browsers:
        browser.close()