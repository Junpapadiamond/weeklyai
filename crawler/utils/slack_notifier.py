"""
Slack Notifier for WeeklyAI
Sends daily digest of trending AI products to Slack

Setup:
1. Go to https://api.slack.com/apps
2. Create a new app → "From scratch"
3. Name it "WeeklyAI Bot", select your workspace
4. Go to "Incoming Webhooks" → Enable it
5. Click "Add New Webhook to Workspace"
6. Select a channel (e.g., #ai-products)
7. Copy the Webhook URL
8. Set environment variable: export SLACK_WEBHOOK_URL="your-webhook-url"
   Or add to .env file in the project root
"""

import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional


class SlackNotifier:
    """Send WeeklyAI notifications to Slack"""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv('SLACK_WEBHOOK_URL')

        if not self.webhook_url:
            # Try loading from .env file
            self._load_dotenv()
            self.webhook_url = os.getenv('SLACK_WEBHOOK_URL')

    def _load_dotenv(self):
        """Load environment variables from .env file"""
        env_paths = [
            os.path.join(os.path.dirname(__file__), '..', '..', '.env'),
            os.path.join(os.path.dirname(__file__), '..', '.env'),
        ]

        for env_path in env_paths:
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip().strip('"\'')
                break

    def is_configured(self) -> bool:
        """Check if Slack webhook is configured"""
        return bool(self.webhook_url)

    def send_message(self, text: str, blocks: List[Dict] = None) -> bool:
        """Send a message to Slack"""
        if not self.webhook_url:
            print("⚠ Slack webhook not configured. Set SLACK_WEBHOOK_URL env variable.")
            return False

        payload = {"text": text}
        if blocks:
            payload["blocks"] = blocks

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 200:
                return True
            else:
                print(f"⚠ Slack error: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"⚠ Slack notification failed: {e}")
            return False

    def send_daily_digest(self, products: List[Dict[str, Any]], top_n: int = 10) -> bool:
        """Send daily digest of trending AI products"""
        if not products:
            return self.send_message("📭 No new AI products today")

        top_products = products[:top_n]
        today = datetime.now().strftime("%Y-%m-%d")

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🔥 WeeklyAI Daily Digest - {today}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Top {len(top_products)} Trending AI Products*\n_Updated just now_"
                }
            },
            {"type": "divider"}
        ]

        for i, product in enumerate(top_products, 1):
            name = product.get('name', 'Unknown')
            desc = product.get('description', '')[:100]
            if len(product.get('description', '')) > 100:
                desc += '...'

            website = product.get('website', '')
            source = product.get('source', 'unknown')
            score = product.get('hot_score', product.get('top_score', 0))

            # Source emoji
            source_emoji = {
                'producthunt': '🚀',
                'hackernews': '🔶',
                'github': '⭐',
                'huggingface': '🤗',
                'tech_news': '📰',
            }.get(source, '🔹')

            # Check if new
            is_new = self._is_new_product(product)
            new_badge = " 🆕" if is_new else ""

            block_text = f"*{i}. {name}*{new_badge} {source_emoji}\n{desc}"
            if website:
                block_text += f"\n<{website}|Visit →>"

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": block_text
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": f"Score: {score}",
                        "emoji": True
                    },
                    "url": website if website else "https://weeklyai.com",
                    "action_id": f"product_{i}"
                }
            })

        # Footer
        blocks.extend([
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📊 Total products tracked: {len(products)} | 🤖 Powered by WeeklyAI"
                    }
                ]
            }
        ])

        text = f"WeeklyAI Daily Digest - {len(top_products)} trending AI products"
        return self.send_message(text, blocks)

    def send_new_product_alert(self, product: Dict[str, Any]) -> bool:
        """Send alert for a new trending product"""
        name = product.get('name', 'Unknown')
        desc = product.get('description', '')[:150]
        website = product.get('website', '')
        source = product.get('source', 'unknown')
        score = product.get('hot_score', 0)

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🆕 *New Trending AI Product*\n\n*{name}* (Score: {score})\n{desc}"
                }
            }
        ]

        if website:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Check it out →",
                            "emoji": True
                        },
                        "url": website,
                        "style": "primary"
                    }
                ]
            })

        return self.send_message(f"New trending: {name}", blocks)

    def send_weekly_summary(self, products: List[Dict[str, Any]], stats: Dict[str, int]) -> bool:
        """Send weekly summary with stats"""
        today = datetime.now().strftime("%Y-%m-%d")

        # Category breakdown
        categories = {}
        for p in products:
            for cat in p.get('categories', ['other']):
                categories[cat] = categories.get(cat, 0) + 1

        top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
        cat_text = "\n".join([f"• {cat}: {count}" for cat, count in top_categories])

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📈 WeeklyAI Weekly Summary",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Total Products*\n{len(products)}"},
                    {"type": "mrkdwn", "text": f"*New This Week*\n{stats.get('new', 0)}"},
                    {"type": "mrkdwn", "text": f"*From GitHub*\n{stats.get('github', 0)}"},
                    {"type": "mrkdwn", "text": f"*From ProductHunt*\n{stats.get('producthunt', 0)}"},
                ]
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Top Categories*\n{cat_text}"
                }
            }
        ]

        return self.send_message("WeeklyAI Weekly Summary", blocks)

    def _is_new_product(self, product: Dict) -> bool:
        """Check if product is new (within 7 days)"""
        from datetime import datetime, timedelta

        first_seen = product.get('first_seen') or product.get('published_at')
        if not first_seen:
            return False

        try:
            if isinstance(first_seen, str):
                # Remove Z suffix and parse
                first_seen = first_seen.rstrip('Z')
                dt = datetime.fromisoformat(first_seen)
            else:
                dt = first_seen

            return (datetime.now() - dt).days <= 7
        except Exception:
            return False


def send_digest_from_file(json_path: str = None, top_n: int = 10) -> bool:
    """Send digest from products_latest.json"""
    if json_path is None:
        json_path = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'products_latest.json'
        )

    if not os.path.exists(json_path):
        print(f"⚠ Products file not found: {json_path}")
        return False

    with open(json_path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    notifier = SlackNotifier()

    if not notifier.is_configured():
        print("\n" + "=" * 50)
        print("Slack Setup Required")
        print("=" * 50)
        print("1. Go to https://api.slack.com/apps")
        print("2. Create new app → From scratch")
        print("3. Enable Incoming Webhooks")
        print("4. Add webhook to your workspace")
        print("5. Set SLACK_WEBHOOK_URL environment variable")
        print("=" * 50 + "\n")
        return False

    return notifier.send_daily_digest(products, top_n)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Test mode - just check configuration
        notifier = SlackNotifier()
        if notifier.is_configured():
            print("✓ Slack webhook configured")
            notifier.send_message("🧪 WeeklyAI test notification - Slack integration working!")
            print("✓ Test message sent")
        else:
            print("✗ Slack webhook not configured")
            print("  Set SLACK_WEBHOOK_URL environment variable")
    else:
        # Send digest
        success = send_digest_from_file()
        if success:
            print("✓ Daily digest sent to Slack")
        else:
            print("✗ Failed to send digest")
