"""
WeeklyAI v2 Frontend E2E Checks

These checks are intended for opt-in local runs against a running Next.js server:

    RUN_FRONTEND_E2E=1 WEEKLYAI_FRONTEND_BASE_URL=http://localhost:4000 pytest tests/test_frontend.py

The default pytest suite skips this module because it requires a browser and a
local frontend server.
"""

import os

import pytest

try:
    from playwright.sync_api import sync_playwright
except ModuleNotFoundError:  # pragma: no cover - depends on local E2E setup
    sync_playwright = None

BASE_URL = os.environ.get("WEEKLYAI_FRONTEND_BASE_URL", "http://localhost:4000")
SCREENSHOT_DIR = "/tmp/weeklyai_tests"


def setup_screenshot_dir():
    import os
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def open_homepage(page):
    """Open homepage with stable readiness checks (avoid flaky networkidle waits)."""
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_selector(".v2-home-root", timeout=15000)
    page.wait_for_selector(".v2-hero-card", timeout=15000)
    page.wait_for_timeout(400)


def check_homepage_loads(page):
    """Test that the v2 homepage loads with the daily-pick structure."""
    print("\n[TEST] Homepage Load")

    open_homepage(page)

    # Check title
    title = page.title()
    assert "WeeklyAI" in title, f"Expected 'WeeklyAI' in title, got: {title}"
    print(f"  ✓ Title: {title}")

    hero = page.locator(".v2-hero-card")
    assert hero.is_visible(), "Hero section not visible"
    print("  ✓ Hero section visible")

    picks_strip = page.locator(".v2-picks-strip")
    assert picks_strip.is_visible(), "Recent picks strip not visible"
    print("  ✓ Recent picks strip visible")

    news_list = page.locator(".v2-news-list")
    assert news_list.is_visible(), "AI news stream not visible"
    print("  ✓ AI news stream visible")

    page.screenshot(path=f"{SCREENSHOT_DIR}/01_homepage.png", full_page=True)
    print(f"  📸 Screenshot saved: {SCREENSHOT_DIR}/01_homepage.png")

    return True


def check_removed_v1_sections(page):
    """Assert removed v1 surfaces do not leak back onto the homepage."""
    print("\n[TEST] Removed v1 Sections")

    open_homepage(page)

    removed_selectors = [
        "#swipeStack",
        ".swipe-card",
        "#weeklySection",
        "#trendingSection",
        "#weeklyProducts",
        "#trendingProducts",
    ]
    for selector in removed_selectors:
        assert page.locator(selector).count() == 0, f"Removed v1 selector still present: {selector}"

    removed_text = ["本周黑马", "更多推荐", "Swipe left and right", "左右滑动"]
    body_text = page.locator("body").inner_text()
    for text in removed_text:
        assert text not in body_text, f"Removed v1 copy still present: {text}"

    print("  ✓ Swipe deck, scoring tiers, and recommendation wall are absent")

    return True


def check_recent_picks(page):
    """Test that recent picks render as a short horizontal strip."""
    print("\n[TEST] Recent Picks")

    open_homepage(page)
    cards = page.locator(".v2-mini-card")
    count = cards.count()
    assert count <= 7, f"Expected at most 7 recent picks, got {count}"

    if count:
        assert cards.first().locator(".v2-mini-name").is_visible(), "Recent pick name not visible"

    print(f"  ✓ Recent picks strip count: {count}")
    page.screenshot(path=f"{SCREENSHOT_DIR}/02_recent_picks.png", full_page=True)

    return True


def check_responsive_design(page):
    """Test responsive design at different viewport sizes"""
    print("\n[TEST] Responsive Design")

    viewports = [
        {"name": "Desktop", "width": 1440, "height": 900},
        {"name": "Tablet", "width": 768, "height": 1024},
        {"name": "Mobile", "width": 375, "height": 812},
    ]

    for vp in viewports:
        page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
        open_homepage(page)
        page.wait_for_timeout(500)

        # Check key elements are visible
        root = page.locator(".v2-home-root")
        hero = page.locator(".v2-hero-card")
        news = page.locator(".v2-news-section")

        assert root.is_visible(), f"Home root not visible at {vp['name']}"
        assert hero.is_visible(), f"Hero not visible at {vp['name']}"
        assert news.is_visible(), f"News stream not visible at {vp['name']}"

        filename = f"{SCREENSHOT_DIR}/09_responsive_{vp['name'].lower()}.png"
        page.screenshot(path=filename, full_page=True)
        print(f"  ✓ {vp['name']} ({vp['width']}x{vp['height']}): Layout OK")

    return True


def check_news_stream(page):
    """Test that the AI news stream displays stable rows or an empty state."""
    print("\n[TEST] AI News Stream")

    page.set_viewport_size({"width": 1440, "height": 900})
    open_homepage(page)
    page.wait_for_timeout(1000)

    news_items = page.locator(".v2-news-item")
    empty_state = page.locator(".v2-strip-empty")
    assert news_items.count() > 0 or empty_state.count() > 0, "News stream has neither rows nor empty state"
    print(f"  ✓ News rows: {news_items.count()} found")

    page.screenshot(path=f"{SCREENSHOT_DIR}/10_news_stream.png", full_page=True)

    return True


def run_all_tests():
    """Run all frontend tests"""
    if sync_playwright is None:
        raise RuntimeError("Python Playwright is not installed. Install it before running frontend E2E checks.")

    setup_screenshot_dir()

    print("=" * 60)
    print("WeeklyAI Frontend Tests")
    print("=" * 60)

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Capture console logs
        page.on("console", lambda msg: None)  # Suppress console output

        tests = [
            ("Homepage Load", check_homepage_loads),
            ("Removed v1 Sections", check_removed_v1_sections),
            ("Recent Picks", check_recent_picks),
            ("Responsive Design", check_responsive_design),
            ("AI News Stream", check_news_stream),
        ]

        for name, test_fn in tests:
            try:
                result = test_fn(page)
                results.append((name, "PASS" if result else "FAIL"))
            except Exception as e:
                results.append((name, f"ERROR: {str(e)[:50]}"))
                print(f"  ✗ Error: {e}")

        browser.close()

    # Print summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    passed = sum(1 for _, r in results if r == "PASS")
    total = len(results)

    for name, result in results:
        status = "✓" if result == "PASS" else "✗"
        print(f"  {status} {name}: {result}")

    print("-" * 60)
    print(f"  Total: {passed}/{total} tests passed")
    print(f"  Screenshots saved to: {SCREENSHOT_DIR}/")
    print("=" * 60)

    return passed == total


def test_frontend_e2e_opt_in():
    if os.environ.get("RUN_FRONTEND_E2E") != "1":
        pytest.skip("Frontend E2E requires RUN_FRONTEND_E2E=1 and a running local frontend server")

    assert run_all_tests()


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
