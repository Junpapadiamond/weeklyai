"""
WeeklyAI Frontend Tests
Tests tinder swipe cards, navigation, search, and responsive design
"""

import json
from playwright.sync_api import sync_playwright, expect

BASE_URL = "http://localhost:3000"
SCREENSHOT_DIR = "/tmp/weeklyai_tests"


def setup_screenshot_dir():
    import os
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def test_homepage_loads(page):
    """Test that homepage loads correctly with all sections"""
    print("\n[TEST] Homepage Load")

    page.goto(BASE_URL)
    page.wait_for_load_state('networkidle')

    # Check title
    title = page.title()
    assert "WeeklyAI" in title, f"Expected 'WeeklyAI' in title, got: {title}"
    print(f"  ✓ Title: {title}")

    # Check hero section
    hero = page.locator('.hero')
    assert hero.is_visible(), "Hero section not visible"
    print("  ✓ Hero section visible")

    # Check navigation
    nav_links = page.locator('.nav-link').all()
    assert len(nav_links) == 3, f"Expected 3 nav links, got {len(nav_links)}"
    print(f"  ✓ Navigation: {len(nav_links)} links found")

    # Check swipe stack
    swipe_stack = page.locator('#swipeStack')
    assert swipe_stack.is_visible(), "Swipe stack not visible"
    print("  ✓ Swipe stack visible")

    page.screenshot(path=f"{SCREENSHOT_DIR}/01_homepage.png", full_page=True)
    print(f"  📸 Screenshot saved: {SCREENSHOT_DIR}/01_homepage.png")

    return True


def test_navigation(page):
    """Test navigation between sections"""
    print("\n[TEST] Navigation")

    page.goto(BASE_URL)
    page.wait_for_load_state('networkidle')

    # Test "本周榜单" navigation
    weekly_link = page.locator('.nav-link[data-section="weekly"]')
    weekly_link.click()
    page.wait_for_timeout(500)

    weekly_section = page.locator('#weeklySection')
    assert weekly_section.is_visible(), "Weekly section not visible after click"
    print("  ✓ Weekly section navigation works")

    page.screenshot(path=f"{SCREENSHOT_DIR}/02_weekly_section.png", full_page=True)

    # Test "搜索" navigation
    search_link = page.locator('.nav-link[data-section="search"]')
    search_link.click()
    page.wait_for_timeout(500)

    search_section = page.locator('#searchSection')
    assert search_section.is_visible(), "Search section not visible after click"
    print("  ✓ Search section navigation works")

    page.screenshot(path=f"{SCREENSHOT_DIR}/03_search_section.png", full_page=True)

    # Test back to "热门推荐"
    trending_link = page.locator('.nav-link[data-section="trending"]')
    trending_link.click()
    page.wait_for_timeout(500)

    trending_section = page.locator('#trendingSection')
    assert trending_section.is_visible(), "Trending section not visible after click"
    print("  ✓ Trending section navigation works")

    return True


def test_tinder_cards(page):
    """Test tinder swipe card functionality"""
    print("\n[TEST] Tinder Swipe Cards")

    page.goto(BASE_URL)
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(1000)  # Wait for cards to load

    # Check if cards are loaded
    swipe_cards = page.locator('.swipe-card').all()
    if len(swipe_cards) == 0:
        print("  ⚠ No swipe cards found (API might have no data)")
        return True

    print(f"  ✓ Found {len(swipe_cards)} swipe cards")

    # Check active card
    active_card = page.locator('.swipe-card.is-active')
    if active_card.count() > 0:
        print("  ✓ Active card found")

        # Get card content
        card_title = active_card.locator('h3').text_content()
        print(f"  ✓ Card title: {card_title}")

        page.screenshot(path=f"{SCREENSHOT_DIR}/04_swipe_card.png")

    # Test Like button
    initial_status = page.locator('#swipeStatus').text_content()
    like_btn = page.locator('#swipeLike')
    like_btn.click()
    page.wait_for_timeout(400)

    new_status = page.locator('#swipeStatus').text_content()
    print(f"  ✓ Like button clicked: {initial_status} → {new_status}")

    page.screenshot(path=f"{SCREENSHOT_DIR}/05_after_like.png")

    # Test Skip button
    skip_btn = page.locator('#swipeNope')
    skip_btn.click()
    page.wait_for_timeout(400)

    final_status = page.locator('#swipeStatus').text_content()
    print(f"  ✓ Skip button clicked: {new_status} → {final_status}")

    page.screenshot(path=f"{SCREENSHOT_DIR}/06_after_skip.png")

    return True


def test_search_functionality(page):
    """Test search functionality"""
    print("\n[TEST] Search Functionality")

    page.goto(BASE_URL)
    page.wait_for_load_state('networkidle')

    # Enter search query
    search_input = page.locator('#searchInput')
    search_input.fill('AI')

    search_btn = page.locator('#searchBtn')
    search_btn.click()

    page.wait_for_timeout(1000)

    # Check search results
    search_section = page.locator('#searchSection')
    assert search_section.is_visible(), "Search section not visible"
    print("  ✓ Search section visible after search")

    result_info = page.locator('#searchResultInfo').text_content()
    print(f"  ✓ Search results: {result_info}")

    page.screenshot(path=f"{SCREENSHOT_DIR}/07_search_results.png", full_page=True)

    # Test category filter
    page.goto(BASE_URL)
    page.wait_for_load_state('networkidle')

    coding_tag = page.locator('.tag-btn[data-category="coding"]')
    coding_tag.click()
    page.wait_for_timeout(1000)

    print("  ✓ Category filter clicked")
    page.screenshot(path=f"{SCREENSHOT_DIR}/08_category_filter.png", full_page=True)

    return True


def test_responsive_design(page):
    """Test responsive design at different viewport sizes"""
    print("\n[TEST] Responsive Design")

    viewports = [
        {"name": "Desktop", "width": 1440, "height": 900},
        {"name": "Tablet", "width": 768, "height": 1024},
        {"name": "Mobile", "width": 375, "height": 812},
    ]

    for vp in viewports:
        page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
        page.goto(BASE_URL)
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(500)

        # Check key elements are visible
        hero = page.locator('.hero')
        nav = page.locator('.navbar')

        assert hero.is_visible(), f"Hero not visible at {vp['name']}"
        assert nav.is_visible(), f"Navbar not visible at {vp['name']}"

        filename = f"{SCREENSHOT_DIR}/09_responsive_{vp['name'].lower()}.png"
        page.screenshot(path=filename, full_page=True)
        print(f"  ✓ {vp['name']} ({vp['width']}x{vp['height']}): Layout OK")

    return True


def test_product_cards_display(page):
    """Test that product cards display correctly"""
    print("\n[TEST] Product Cards Display")

    page.set_viewport_size({"width": 1440, "height": 900})
    page.goto(BASE_URL)
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(1500)  # Wait for products to load

    # Check trending products
    trending_cards = page.locator('#trendingProducts .product-card').all()
    print(f"  ✓ Trending cards: {len(trending_cards)} found")

    if len(trending_cards) > 0:
        first_card = trending_cards[0]

        # Check card elements
        has_logo = first_card.locator('.product-logo').count() > 0
        has_name = first_card.locator('.product-name').count() > 0
        has_desc = first_card.locator('.product-description').count() > 0

        print(f"  ✓ Card structure: logo={has_logo}, name={has_name}, desc={has_desc}")

    # Navigate to weekly and check
    page.locator('.nav-link[data-section="weekly"]').click()
    page.wait_for_timeout(1000)

    weekly_items = page.locator('#weeklyProducts .product-list-item').all()
    print(f"  ✓ Weekly list items: {len(weekly_items)} found")

    page.screenshot(path=f"{SCREENSHOT_DIR}/10_weekly_list.png", full_page=True)

    return True


def run_all_tests():
    """Run all frontend tests"""
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
            ("Homepage Load", test_homepage_loads),
            ("Navigation", test_navigation),
            ("Tinder Cards", test_tinder_cards),
            ("Search", test_search_functionality),
            ("Responsive Design", test_responsive_design),
            ("Product Cards", test_product_cards_display),
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


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
