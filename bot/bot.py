import urllib.request
import xml.etree.ElementTree as ET
import time
import os
import urllib.parse
import json
import html
from dotenv import load_dotenv
from html.parser import HTMLParser

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SENT_FILE = "sent_links.txt"


class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []

    def handle_data(self, d):
        self.result.append(d)

    def get_data(self):
        return ''.join(self.result)

def strip_tags(html_text):
    s = HTMLStripper()
    s.feed(html_text)
    return s.get_data()

KEYWORDS = [
    "it", "technology", "tech", "digital", "information technology", "ict",
    "software", "developer", "development", "programming", "coding",
    "engineering", "engineer", "dev", "devops", "debugging",
    "software engineer", "fullstack", "frontend", "backend",
    "qa engineer", "tester", "business analyst", "ba", "product owner",
    "product manager", "scrum master", "agile coach", "project manager",
    "python", "java", "javascript", "typescript", "c#", "c++", "go",
    "rust", "ruby", "php", "kotlin", "swift", "sql", "nosql",
    "docker", "kubernetes", "git", "github", "bitbucket", "jenkins", "jira",
    "vscode", "visual studio", "intellij", "eclipse", "postman", "swagger",
    "artificial intelligence", "ai", "machine learning", "ml", "deep learning",
    "data", "data science", "data analyst", "data engineer", "nlp", "computer vision",
    "chatgpt", "openai", "llm", "big data", "analytics", "model training",
    "cloud", "aws", "azure", "gcp", "cloud engineer", "cloud architecture",
    "system architecture", "microservices", "monolith", "serverless", "api",
    "cybersecurity", "security", "encryption", "zero trust", "vpn", "firewall",
    "penetration testing", "network", "sre", "infrastructure", "it operations",
    "agile", "scrum", "kanban", "waterfall", "sdlc", "ci/cd", "ux", "ui", "design thinking",
    "blockchain", "web3", "metaverse", "iot", "5g", "edge computing"
]

RSS_FEEDS = [
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.wired.com/feed/rss",
    "https://www.technologyreview.com/feed/",
    "https://www.engadget.com/rss.xml",
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://www.zdnet.com/news/rss.xml",
    "https://www.cnet.com/rss/news/",
]

def matched_keywords(text):
    if not text:
        return []
    text_lower = text.lower()
    return [kw for kw in KEYWORDS if kw in text_lower]

def load_sent_links():
    if not os.path.exists(SENT_FILE):
        return set()
    with open(SENT_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f.readlines())

def save_sent_link(link):
    with open(SENT_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")

def send_to_telegram(title, link, summary, matched):
    clean_title = html.escape(strip_tags(title))
    clean_summary = html.escape(strip_tags(summary[:300])) if summary else ""
    clean_keywords = html.escape(', '.join(matched))
    clean_link = html.escape(link)

    message = f"<b>{clean_title}</b>\n"
    if clean_summary:
        message += f"<i>{clean_summary}</i>\n"
    if matched:
        message += f"\n<b>Matched keywords:</b> {clean_keywords}\n"
    message += f"{clean_link}"

    if len(message) > 4000:
        message = message[:3990] + "…"

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    print("DEBUG MSG:", message[:300])
    print("DEBUG LEN:", len(message))

    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req) as resp:
        response = resp.read()
        return json.loads(response)

def fetch_rss(url):
    with urllib.request.urlopen(url) as resp:
        content = resp.read()
        root = ET.fromstring(content)
        return root.findall(".//item")

def check_feeds():
    sent = load_sent_links()
    for feed in RSS_FEEDS:
        try:
            items = fetch_rss(feed)
            for item in items[:5]:
                title = item.find("title").text or ""
                link = item.find("link").text or ""
                description_elem = item.find("description")
                summary = description_elem.text if description_elem is not None else ""
                combined = f"{title} {summary}".lower()

                if "promocode" in combined:
                    continue

                matched = matched_keywords(combined)

                if link not in sent and matched:
                    send_to_telegram(title, link, summary, matched)
                    save_sent_link(link)
                    print(f"✅ Sent: {title}")
                    time.sleep(2)
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    try:
        while True:
            print("🕒 Checking...")
            check_feeds()
            print("⏳ Waiting 1 hour...")
            time.sleep(3600)
    except KeyboardInterrupt:
        print("🛑 BOT was stopped.")
