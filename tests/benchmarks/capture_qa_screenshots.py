"""
Automated Browser QA and Screenshot Capture Script for AASI Phase 2.
Captures high-resolution evidence across all 10 required operational and UI states.
"""

import time
from playwright.sync_api import sync_playwright


def send_message(page, text: str):
    """Fill the textarea, click SEND, and wait for assistant response."""
    initial_count = page.locator(".message-row.assistant").count()
    textarea = page.locator("textarea.chat-input")
    textarea.click()
    textarea.fill(text)
    time.sleep(0.5)
    page.locator("button.btn-send").click()
    page.wait_for_function(
        f"document.querySelectorAll('.message-row.assistant').length > {initial_count}",
        timeout=60000,
    )
    time.sleep(2)


def reset_chat(page):
    """Click CLEAR button to reset session."""
    page.locator("button:has-text('CLEAR')").click()
    time.sleep(1)


def capture_all_screenshots():
    print("Launching Edge browser via Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        # ----------------------------------------------------------------------
        # 1. 01-home.png: Initial AASI Interface
        # ----------------------------------------------------------------------
        print("Capturing 01-home.png...")
        page.goto("http://localhost:3000")
        page.wait_for_selector(".app-header")
        time.sleep(2)
        page.screenshot(path="docs/qa/screenshots/01-home.png")

        # ----------------------------------------------------------------------
        # 2. 02-conceptual.png: Conceptual Question Response
        # ----------------------------------------------------------------------
        print("Capturing 02-conceptual.png...")
        send_message(page, "What is a Hohmann transfer and when is it used?")
        page.screenshot(path="docs/qa/screenshots/02-conceptual.png")

        # ----------------------------------------------------------------------
        # 3. 03-circular-orbit.png: Circular Orbit Calculation
        # ----------------------------------------------------------------------
        print("Capturing 03-circular-orbit.png...")
        reset_chat(page)
        send_message(
            page,
            "Calculate the orbital velocity and period for a satellite in circular Earth orbit at 500 km altitude.",
        )
        page.screenshot(path="docs/qa/screenshots/03-circular-orbit.png")

        # ----------------------------------------------------------------------
        # 4. 04-hohmann.png: Hohmann Transfer Calculation
        # ----------------------------------------------------------------------
        print("Capturing 04-hohmann.png...")
        reset_chat(page)
        send_message(
            page,
            "Compute the delta-v needed for a Hohmann transfer from 200 km to 500 km circular Earth orbit.",
        )
        page.screenshot(path="docs/qa/screenshots/04-hohmann.png")

        # ----------------------------------------------------------------------
        # 5. 05-rocket-equation.png: Rocket Equation Calculation
        # ----------------------------------------------------------------------
        print("Capturing 05-rocket-equation.png...")
        reset_chat(page)
        send_message(
            page,
            "A rocket has an Isp of 350 s, initial mass of 10000 kg, and dry mass of 3000 kg. What is its delta-v?",
        )
        page.screenshot(path="docs/qa/screenshots/05-rocket-equation.png")

        # ----------------------------------------------------------------------
        # 6. 06-tool-trace.png: Tool Execution Trace
        # ----------------------------------------------------------------------
        print("Capturing 06-tool-trace.png...")
        page.screenshot(path="docs/qa/screenshots/06-tool-trace.png")

        # ----------------------------------------------------------------------
        # 7. 07-verification.png: SymPy Verification Display
        # ----------------------------------------------------------------------
        print("Capturing 07-verification.png...")
        card = page.locator(".calc-card").first
        if card.count() > 0:
            card.screenshot(path="docs/qa/screenshots/07-verification.png")
        else:
            page.screenshot(path="docs/qa/screenshots/07-verification.png")

        # ----------------------------------------------------------------------
        # 8. 08-validation-error.png: Validation Error State
        # ----------------------------------------------------------------------
        print("Capturing 08-validation-error.png...")
        reset_chat(page)
        send_message(page, "Calculate circular orbit at -500 km altitude.")
        page.screenshot(path="docs/qa/screenshots/08-validation-error.png")

        # ----------------------------------------------------------------------
        # 9. 09-clarification.png: Missing-Parameter Clarification State
        # ----------------------------------------------------------------------
        print("Capturing 09-clarification.png...")
        reset_chat(page)
        send_message(page, "How fast does a satellite move?")
        page.screenshot(path="docs/qa/screenshots/09-clarification.png")

        # ----------------------------------------------------------------------
        # 10. 10-mobile.png: Mobile Responsive View
        # ----------------------------------------------------------------------
        print("Capturing 10-mobile.png...")
        context_mobile = browser.new_context(viewport={"width": 375, "height": 812})
        page_mobile = context_mobile.new_page()
        page_mobile.goto("http://localhost:3000")
        time.sleep(2)
        send_message(page_mobile, "Calculate circular orbit velocity at 500 km altitude.")
        page_mobile.screenshot(path="docs/qa/screenshots/10-mobile.png")

        browser.close()
        print("All 10 QA screenshots captured successfully!")


if __name__ == "__main__":
    capture_all_screenshots()
