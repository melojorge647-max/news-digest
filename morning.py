import smtplib
import datetime
import urllib.request
import re
import os
from email.mime.text import MIMEText
from email.utils import parsedate_to_datetime

GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
RECIPIENTS = ["melojorge647@gmail.com", "jorge@jmelomedia.com", "info@jmelomedia.com"]

FEEDS = [
    ("Search Engine Land",   "https://searchengineland.com/feed"),
    ("Search Engine Journal","https://www.searchenginejournal.com/feed/"),
    ("SE Roundtable",        "https://www.seroundtable.com/feed.xml"),
    ("Social Media Examiner","https://www.socialmediaexaminer.com/feed/"),
    ("Marketing Brew",       "https://www.marketingbrew.com/feed.xml"),
    ("Moz Blog",             "https://moz.com/blog/feed"),
    ("Semrush Blog",         "https://www.semrush.com/blog/feed/"),
    ("Ahrefs Blog",          "https://ahrefs.com/blog/feed/"),
    ("Digiday",              "https://digiday.com/feed/"),
    ("WP Tavern",            "https://wptavern.com/feed"),
    ("Smashing Magazine",    "https://www.smashingmagazine.com/feed/"),
    ("CSS-Tricks",           "https://css-tricks.com/feed/"),
    ("Web Designer Depot",   "https://webdesignerdepot.com/feed/"),
    ("TechCrunch",           "https://techcrunch.com/feed/"),
]

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
    "wordpress", "wix", "squarespace", "webflow", "lovable", "on-page",
    "on page", "page speed", "core web vitals", "website builder",
]

LOW_VALUE_WORDS = [
    "how to", "guide", "tutorial", "tips for", "best practices",
    "checklist", "step by step", "beginners", "101",
]

# At least one article must match one of these topic groups
GUARANTEED_TOPICS = [
    ["wordpress", "wix", "squarespace", "webflow", "lovable", "website builder",
     "ai website", "html", "web design", "web development", "website design",
     "on-page seo", "on page seo", "page speed", "core web vitals", "cms"],
    ["instagram algorithm", "facebook algorithm", "instagram update", "facebook update",
     "meta algorithm", "instagram feature", "facebook feature", "reels", "stories algorithm"],
]


def clean_text(raw):
    """Strip HTML tags, decode entities, collapse whitespace."""
    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"&#\d+;", "", text)
    text = re.sub(r"&[a-zA-Z]+;", "", text)
    text = re.sub(r"<p>|</p>|<img[^>]*>|<a[^>]*>|</a>", " ", text)
    text = re.sub(r"The post .* appeared first on .*\.", "", text)
    text = re.sub(r"\[.*?\]", "", text)  # remove [shortcodes]
    text = re.sub(r"\s+", " ", text).strip()
    return text


def to_4_sentences(text):
    """Return up to 4 sentences from a block of text."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    return " ".join(sentences[:4])


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
            desc_m  = re.search(r"<description><!\[CDATA\[(.*?)\]\]></description>|<description>(.*?)</description>", item, re.DOTALL)
            date_m  = re.search(r"<pubDate>(.*?)</pubDate>", item)
            if not title_m:
                continue
            t = (title_m.group(1) or title_m.group(2) or "").strip()
            l = ""
            if link_m:
                l = (link_m.group(1) or link_m.group(2) or "").strip()
                l = re.sub(r"\s+", "", l)
            d = ""
            if desc_m:
                raw = (desc_m.group(1) or desc_m.group(2) or "").strip()
                d = to_4_sentences(clean_text(raw))
            pub = ""
            if date_m:
                try:
                    dt = parsedate_to_datetime(date_m.group(1).strip())
                    pub = dt.strftime("%b %d, %Y %I:%M %p %Z")
                except Exception:
                    pub = date_m.group(1).strip()
            if t and len(t) > 15:
                results.append((source, t, l, d, pub))
        return results[:10]
    except Exception as e:
        print(f"  Failed to fetch {source}: {e}")
        return []


def score(item):
    t = item[1].lower()
    s = 0
    for w in HIGH_VALUE_WORDS:
        if w in t:
            s += 2
    for w in LOW_VALUE_WORDS:
        if w in t:
            s -= 3
    return s


def matches_topic(title, keywords):
    t = title.lower()
    return any(kw in t for kw in keywords)


def main():
    date_str = datetime.date.today().strftime("%B %d, %Y")
    offset = 0
    slot = "Morning"
    print(f"Fetching headlines for {date_str} ({slot} edition)...")

    all_headlines = []
    for source, url in FEEDS:
        headlines = fetch_headlines(source, url)
        print(f"  {source}: {len(headlines)} headlines")
        all_headlines.extend(headlines)

    if slot == "Evening":
        # Evening: sort by most recently published so you get fresh articles from the day
        def pub_key(item):
            try:
                from email.utils import parsedate_to_datetime as p
                return p(item[4]) if item[4] else datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
            except Exception:
                return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
        all_headlines.sort(key=pub_key, reverse=True)
    else:
        # Morning: sort by relevance score
        all_headlines.sort(key=score, reverse=True)

    selected = []
    used_indices = set()

    # Reserve 1 guaranteed slot per topic group
    for topic_keywords in GUARANTEED_TOPICS:
        for i, h in enumerate(all_headlines):
            if i not in used_indices and matches_topic(h[1], topic_keywords):  # h[1] is title
                selected.append(h)
                used_indices.add(i)
                break

    # Fill remaining slots up to 10 with top-scored articles
    for i, h in enumerate(all_headlines):
        if len(selected) >= 10:
            break
        if i not in used_indices and score(h) >= 0:
            selected.append(h)
            used_indices.add(i)

    # Fall back to top unfiltered if still not enough
    for i, h in enumerate(all_headlines):
        if len(selected) >= 10:
            break
        if i not in used_indices:
            selected.append(h)
            used_indices.add(i)

    if not selected:
        print("No headlines fetched — aborting.")
        return

    lines = [f"DAILY MARKETING NEWS - {date_str}", ""]
    for i, (source, title, link, summary, pub) in enumerate(selected, 1):
        lines.append(f"{i}. [{source}] {title}")
        if pub:
            lines.append(f"   Published: {pub}")
        if link:
            lines.append(f"   {link}")
        if summary:
            lines.append(f"   {summary}")
        lines.append("")
    lines += ["---", "Your daily Claude marketing digest"]
    body = "\n".join(lines)

    print("\nDigest preview:")
    print(body)
    print()

    msg = MIMEText(body)
    msg["Subject"] = f"Daily Marketing News ({slot}) - {date_str}"
    msg["From"] = GMAIL_USER
    msg["To"] = ", ".join(RECIPIENTS)

    with smtplib.SMTP("smtp.gmail.com", 587) as s:
        s.starttls()
        s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        s.sendmail(GMAIL_USER, RECIPIENTS, msg.as_string())

    print("Email sent to:", ", ".join(RECIPIENTS))


if __name__ == "__main__":
    main()
