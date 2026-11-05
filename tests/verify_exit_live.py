"""Live UI verification of the FillBlank exit fix against the running backend.

Drives the served SPA (http://127.0.0.1:8000) with the installed Chrome via
Playwright, reproducing the reported bug 10 times:
  enter 挖空填词 -> click 退出 (back arrow) -> must return to the game list,
  never re-mount / re-load the game.

Run while WordMaster.exe is running.
"""

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
ROUNDS = 10


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page()
        page.goto(f"{BASE}/games", wait_until="networkidle")

        assert page.locator("h1:has-text('小游戏')").count() == 1, "game list not shown"

        passed = 0
        for i in range(ROUNDS):
            # Enter the fill-blank game.
            page.locator("button:has-text('挖空填词')").first.click()
            # Playing phase: the answer input appears (placeholder 输入单词...).
            page.wait_for_selector("input[placeholder*='输入单词']", timeout=10000)
            # Click the top-left exit (back) arrow.
            page.locator("button[aria-label='Back']").first.click()
            # Must return to the game list (字母拼词 card visible).
            page.wait_for_selector("h1:has-text('小游戏')", timeout=5000)
            # The game must be fully gone — no answer input, no 检查答案 button.
            still_in_game = (
                page.locator("input[placeholder*='输入单词']").count() > 0
                or page.locator("button:has-text('检查答案')").count() > 0
            )
            if still_in_game:
                print(f"  round {i + 1}: FAIL (game still mounted)")
            else:
                passed += 1
                print(f"  round {i + 1}: OK  (returned to game list)")

        print(f"  SUMMARY: {passed}/{ROUNDS} exits returned to the game list")
        browser.close()
        return 0 if passed == ROUNDS else 1


if __name__ == "__main__":
    raise SystemExit(main())
