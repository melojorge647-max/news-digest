import smtplib
import datetime
import urllib.request
import re
import os
from email.mime.text import MIMEText

GMAIL_USER = os.environ.get("GMAIL_USER", "melojorge647@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "jotzxlsnfqtzynxe")
RECIPIENTS = ["melojorge647@gmail.com", "jorge@jmelomedia.com", "info@jmelomedia.com"]

# High-quality industry news sources focused on updates, changes, announcements
FEEDS = [
    ("Search Engine Land", "https://searchengineland.com/feed"),
    ("Search Engine Journal", "https://www.searchenginejournal.com/feed/"),
    ("SE Roundtable",        "https://www.seroundtable.com/feed.xml"),
    ("Social Media Examiner","https://www.socialmediaexaminer.com/feed/"),
    ("Marketing Brew",       "https://www.marketingbrew.com/feed.xml"),
    ("Moz Blog",             "https://moz.com/blog/feed"),
    ("Semrush Blog",         "https://www.semrush.com/blog/feed/"),
    ("Ahrefs Blog",          "https://ahrefs.com/blog/feed/"),
    ("Digiday",              "https://digiday.com/feed/"),
    ("The Verge Tech",       "https://www.theverge.com/rss/index.xml"),
]

# Words that signal impactful industry news
HIGH_VALUE_WORDS = [
    "update", "new", "launch", "release", "change", "announces", "announced",
    "algorithm", "core update", "rollout", "rolling out", "feature", "test",
    "testing", "ai", "artificial intelligence", "chatgpt", "gemini", "openai",
    "google search", "google ads", "meta ads", "tiktok", "linkedin", "instagram",
    "facebook", "youtube", "bing", "perplexity", "ai overview", "sge",
    "generative", "search generative", "local service", "lsa", "performance max",
    "pmax", "smart bidding", "campaign", "ban", "policy", "penalty", "deindex",
    "ranking", "serp", "zero click", "featured snippet", "knowledge panel",
    "helpful content", "spam", "manual action", "broad core", "leak",
    "api", "integration", "platform", "tool", "software", "breaking",
]

# Words that signal generic how-to guides (lower priority)
LOW_VALUE_WORDS = [
    "how to", "guide", "tutorial", "tips for", "best practices",
    "checklist", "step by step", "beginners", "101",
]


def fetch_headlines(source, url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            xml = r.read().decode("utf-8", errors="ignore")
        items = re.findall(r"<item>(.*?)</item>", xml, re.DOTALL)
        results = []
        for item in items:
            title_m = re.search(r"<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>", item)
            link_m  = re.search(r"<link>(.*?)</link>|<link\s[^>]*href=[\"'](.*?)[\"']", item, re.DOTALL)
            if not title_m:
                continue
            t = (title_m.group(1) or title_m.group(2) or "").strip()
            l = ""
            if link_m:
                l = (link_m.group(1) or link_m.group(2) or "").strip()
                l = re.sub(r"\s+", "", l)  # remove whitespace/newlines in URL
            if t and len(t) > 15:
                results.append((source, t, l))
        return results[:10]
    except Exception as e:
        print(f"  Failed to fetch {source}: {e}")
        return []


def score(title):
    t = title.lower()
    s = 0
    for w in HIGH_VALUE_WORDS:
        if w in t:
            s += 2
    for w in LOW_VALUE_WORDS:
        if w in t:
            s -= 3  # penalize generic guides
    return s


def main():
    date_str = datetime.date.today().strftime("%B %d, %Y")
    print(f"Fetching headlines for {date_str}...")

    all_headlines = []
    for source, url in FEEDS:
        headlines = fetch_headlines(source, url)
        print(f"  {source}: {len(headlines)} headlines")
        all_headlines.extend(headlines)

    # Sort by relevance score, filter out negatively scored items
    all_headlines.sort(key=lambda x: score(x[1]), reverse=True)
    top = [h for h in all_headlines if score(h[1]) >= 0][:8]

    # Fall back to top unfiltered if not enough
    if len(top) < 5:
        top = all_headlines[:8]

    if not top:
        print("No headlines fetched — aborting.")
        return

    lines = [f"DAILY MARKETING NEWS - {date_str}", ""]
    for i, (source, title, link) in enumerate(top, 1):
        lines.append(f"{i}. [{source}]")
        lines.append(f"   {title}")
        if link:
            lines.append(f"   {link}")
        lines.append("")
    lines += ["---", "Your daily Claude marketing digest"]
    body = "\n".join(lines)

    print("\nDigest preview:")
    print(body)
    print()

    msg = MIMEText(body)
    msg["Subject"] = f"Daily Marketing News - {date_str}"
    msg["From"] = GMAIL_USER
    msg["To"] = ", ".join(RECIPIENTS)

    with smtplib.SMTP("smtp.gmail.com", 587) as s:
        s.starttls()
        s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        s.sendmail(GMAIL_USER, RECIPIENTS, msg.as_string())

    print("Email sent to:", ", ".join(RECIPIENTS))


if __name__ == "__main__":
    main()
