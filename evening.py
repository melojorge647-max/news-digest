import smtplib
import datetime
import urllib.request
import re
import os
import base64
import json
from email.mime.text import MIMEText
from email.utils import parsedate_to_datetime

GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
RECIPIENTS = ["melojorge647@gmail.com", "jorge@jmelomedia.com", "info@jmelomedia.com", "camrynalvares03@gmail.com"]

GITHUB_REPO   = "melojorge647-max/news-digest"
SENT_FILE     = "sent_urls.txt"
SENT_MAX_HOURS = 80  # Keep URLs excluded for slightly more than 3 days

FEEDS = [
    # SEO / Search
    ("Search Engine Land",    "https://searchengineland.com/feed"),
    ("Search Engine Journal", "https://www.searchenginejournal.com/feed/"),
    ("SE Roundtable",         "https://www.seroundtable.com/feed.xml"),
    ("Moz Blog",              "https://moz.com/blog/feed"),
    ("Google Search Central", "https://developers.google.com/search/blog/feeds/blog.xml"),
    # Paid Ads
    ("WordStream",            "https://www.wordstream.com/blog/feed"),
    ("PPC Hero",              "https://www.ppchero.com/feed/"),
    # Social Media
    ("Social Media Examiner", "https://www.socialmediaexaminer.com/feed/"),
    ("Social Media Today",    "https://www.socialmediatoday.com/rss/"),
    ("Sprout Social",         "https://sproutsocial.com/insights/feed/"),
    # General Marketing (news-focused)
    ("Marketing Brew",        "https://www.marketingbrew.com/feed.xml"),
    ("MarTech",               "https://martech.org/feed/"),
    ("AdWeek",                "https://www.adweek.com/feed/"),
    ("The Drum",              "https://www.thedrum.com/rss"),
    ("Digiday",               "https://digiday.com/feed/"),
    # Web / CMS
    ("WP Tavern",             "https://wptavern.com/feed"),
    ("WordPress.org News",    "https://wordpress.org/news/feed/"),
    # Local SEO
    ("BrightLocal",           "https://www.brightlocal.com/blog/feed/"),
    ("Sterling Sky",          "https://sterlingsky.ca/feed/"),
    ("Near Media",            "https://www.nearmedia.co/feed/"),
    # Tools
    ("Semrush Blog",          "https://www.semrush.com/blog/feed/"),
]

BREAKING_WORDS = [
    "algorithm update", "core update", "broad core", "manual action", "penalty",
    "rolling out", "rolls out", "rolled out", "new feature", "breaking", "major change",
    "policy change", "ban", "deindex", "spam update", "ranking update",
    "serp change", "leaked", "ranking factor", "search ranking change",
    "helpful content", "google confirms", "google says", "google warns", "google announces",
    "meta announces", "meta confirms", "meta update", "meta launches",
    "facebook announces", "facebook update", "facebook algorithm", "facebook launches",
    "instagram announces", "instagram launches", "instagram update", "instagram algorithm",
    "reels update", "feed update", "feed algorithm",
    "linkedin announces", "linkedin launches", "linkedin update", "linkedin algorithm",
    "tiktok announces", "tiktok launches", "tiktok update", "tiktok algorithm",
    "tiktok ban", "tiktok changes",
    "youtube announces", "youtube launches", "youtube update", "youtube algorithm",
    "youtube monetization", "youtube changes",
    "x announces", "twitter announces", "x update", "twitter update",
    "x algorithm", "twitter algorithm", "x launches",
    "snapchat announces", "snapchat update", "pinterest announces", "pinterest update",
    "threads announces", "threads update", "threads algorithm",
    "bing update", "bing announces", "bing algorithm", "bing changes",
    "search engine update", "search update",
    "google ads update", "meta ads update", "ad policy change", "ads announcement",
    "performance max update", "smart bidding update",
    "paying creators", "creator fund", "creator monetization", "creator economy",
    "bonus program", "revenue share", "creator program", "creator payout",
    "ad revenue sharing", "platform pays", "monetize creators",
    "zuckerberg", "adam mosseri", "ryan roslansky", "sundar pichai", "satya nadella",
    "ceo says", "ceo announces", "ceo confirms",
    "google business profile update", "gbp update", "map pack change", "local pack update",
    "google maps update", "local search update",
    # News-signal words
    "algorithm change", "ranking change", "new ad format", "feature update",
    "platform update", "now live", "available now", "in testing", "introduces new",
    "deprecating", "shutting down", "enforcement update", "officially launches",
    "changes to", "now rolling", "test new",
    # Legal / regulatory / privacy
    "ftc", "antitrust", "doj sues", "regulators", "fined", "settlement",
    "privacy update", "third-party cookies", "cookie deprecation",
    "ios update", "apple privacy", "tracking changes", "data privacy",
    "gdpr", "class action",
    # Business moves in ad/marketing tech
    "acquires", "acquisition", "merges with", "merger", "shuts down", "layoffs",
    "raises funding", "ipo", "goes public", "buys", "purchased by",
    # Research / data / exclusive findings
    "new study", "new research", "data shows", "report finds", "survey finds",
    "according to new", "just announced", "just released", "exclusive:", "breaking:",
    "first look", "new report", "industry report", "benchmark report",
    "study reveals", "research reveals", "findings show", "data reveals",
    "percent of marketers", "percent of businesses", "marketers say",
]

MARKETING_WORDS = [
    "seo", "search engine", "google search", "google ads", "meta ads", "facebook ads",
    "instagram ads", "linkedin ads", "tiktok ads", "local service ads", "lsa",
    "performance max", "pmax", "smart bidding", "email marketing", "social media",
    "content marketing", "link building", "backlink", "keyword", "serp", "ranking",
    "local seo", "on-page", "on page", "technical seo", "page speed", "core web vitals",
    "conversion rate", "landing page", "ppc", "paid search", "paid social",
    "wordpress", "wix", "squarespace", "webflow", "website design", "web development",
    "google analytics", "google search console", "google business profile",
    "featured snippet", "knowledge panel", "zero click",
    "gbp", "map pack", "local pack", "local search", "local ranking",
    "google maps ranking", "plumber", "roofer", "hvac", "electrician", "contractor",
    "home service", "service area", "review management", "citation", "local citation",
    "near me", "local 3-pack", "local business", "google reviews",
]

AI_WORDS = [
    "artificial intelligence", "chatgpt", "openai", "gemini", "claude",
    "llm", "large language model", "ai overview", "ai search", "generative ai",
    "perplexity", "copilot", "gpt", "machine learning",
]

LOW_VALUE_WORDS = [
    "how to", "guide to", "tutorial", "tips for", "best practices",
    "checklist", "step by step", "beginners guide", "101", "complete guide",
    "ultimate guide", "everything you need to know", "what is", "explained",
    "introduction to", "getting started", "learn how", "a beginner",
    "the complete", "the ultimate", "top tips", "quick tips", "pro tips",
    "expert tips", "here's how", "for beginners", "you need to know",
]

STORY_WORDS = [
    "opinion", "my experience", "case study", "interview with", "podcast",
    "webinar", "roundup", "weekly recap", "monthly recap", "predictions for",
    "lessons learned", "retrospective", "thought leadership", "personal story",
    "i tested", "we tested",
]

REQUIRED_KEYWORDS = [
    # SEO / search
    "seo", "search engine optimization", "google search", "search ranking",
    "serp", "backlink", "link building", "keyword research", "on-page seo",
    "technical seo", "core web vitals", "page speed", "google algorithm",
    "featured snippet", "knowledge panel", "search console", "sitemap",
    # Google products
    "google ads", "google analytics", "google business profile",
    "google maps", "google shopping", "google my business",
    # Paid ads
    "ppc", "paid search", "paid social", "facebook ads", "instagram ads",
    "meta ads", "tiktok ads", "linkedin ads", "youtube ads",
    "local service ads", "performance max", "smart bidding", "ad campaign",
    "ad creative", "ad spend", "roas", "cost per click", "cpc", "cpm",
    # Social media marketing
    "social media marketing", "instagram marketing", "facebook marketing",
    "tiktok marketing", "linkedin marketing", "youtube marketing",
    "social media algorithm", "instagram algorithm", "facebook algorithm",
    "tiktok algorithm", "reels", "content creator", "creator monetization",
    # Email / CRO
    "email marketing", "email campaign", "open rate", "click rate",
    "conversion rate", "landing page", "a/b test", "cro",
    # Web / CMS
    "wordpress", "wix", "squarespace", "webflow", "website design",
    "web development", "website builder", "cms",
    # Local SEO / service biz
    "local seo", "local search", "map pack", "local pack", "gbp",
    "google reviews", "review management", "local ranking", "citation",
    "plumber marketing", "hvac marketing", "roofer marketing",
    "contractor marketing", "home service marketing", "local service ads",
    # Platforms / tools
    "shopify", "ecommerce marketing", "marketing automation",
    "marketing strategy", "digital marketing", "marketing campaign",
    # Social media for small biz / marketers
    "instagram update", "facebook update", "tiktok update", "linkedin update",
    "youtube update", "threads update", "social media update",
    "instagram feature", "facebook feature", "tiktok feature",
    "organic reach", "engagement rate", "hashtag strategy",
    "social media ads", "boosted post", "paid promotion",
    "small business marketing", "business page", "creator tools",
]

GUARANTEED_TOPICS = [
    ["wordpress", "wix", "squarespace", "webflow", "lovable", "website builder",
     "web design", "web development", "website design", "page speed", "core web vitals", "cms"],
    ["instagram", "facebook", "meta ads", "reels", "social media"],
    ["google business profile", "gbp", "map pack", "local pack", "local seo",
     "local search", "local ranking", "plumber", "roofer", "hvac", "electrician",
     "home service", "contractor", "near me", "local 3-pack", "local citation",
     "google reviews", "service area business"],
    ["home service", "contractor marketing", "plumber", "hvac", "roofer",
     "electrician", "landscaper", "lawn care", "service business",
     "local service ads", "contractor leads", "home improvement",
     "trade business", "field service", "home services"],
]

MAX_ARTICLES  = 13
MAX_AGE_DAYS  = 3
MIN_SCORE     = 10


# ---------------------------------------------------------------------------
# Sent-URL tracking via GitHub Contents API (no git operations)
# ---------------------------------------------------------------------------

def _gh_request(method, path, payload=None):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def load_sent_urls():
    """Return set of URLs sent within the past SENT_MAX_HOURS hours."""
    if not GITHUB_TOKEN:
        return set()
    try:
        resp = _gh_request("GET", SENT_FILE)
        raw = base64.b64decode(resp["content"]).decode("utf-8")
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=SENT_MAX_HOURS)
        urls = set()
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t", 1)
            if len(parts) == 2:
                try:
                    ts = datetime.datetime.fromisoformat(parts[0])
                    if ts >= cutoff:
                        urls.add(parts[1])
                except Exception:
                    pass
        print(f"  Loaded {len(urls)} previously sent URLs (last {SENT_MAX_HOURS}h)")
        return urls
    except Exception as e:
        print(f"  Could not load sent URLs: {e}")
        return set()


def save_sent_urls(new_urls):
    """Append new_urls with timestamps; prune entries older than SENT_MAX_HOURS."""
    if not GITHUB_TOKEN or not new_urls:
        return
    try:
        try:
            resp = _gh_request("GET", SENT_FILE)
            existing_raw = base64.b64decode(resp["content"]).decode("utf-8")
            sha = resp["sha"]
        except Exception:
            existing_raw = ""
            sha = None

        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=SENT_MAX_HOURS)
        kept = []
        for line in existing_raw.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t", 1)
            if len(parts) == 2:
                try:
                    if datetime.datetime.fromisoformat(parts[0]) >= cutoff:
                        kept.append(line)
                except Exception:
                    pass

        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        for url in new_urls:
            if url:
                kept.append(f"{now_str}\t{url}")

        content = "\n".join(kept) + "\n"
        payload = {
            "message": f"chore: log {len(new_urls)} sent URLs",
            "content": base64.b64encode(content.encode()).decode(),
            "committer": {"name": "digest-bot", "email": "digest-bot@noreply"},
        }
        if sha:
            payload["sha"] = sha
        _gh_request("PUT", SENT_FILE, payload)
        print(f"  Saved {len(new_urls)} sent URLs")
    except Exception as e:
        print(f"  Could not save sent URLs: {e}")


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def is_marketing_relevant(title, summary):
    combined = (title + " " + summary).lower()
    return any(kw in combined for kw in REQUIRED_KEYWORDS)


def is_ai_article(title, summary):
    combined = (title + " " + summary).lower()
    return any(kw in combined for kw in AI_WORDS)


def clean_text(raw):
    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"&#\d+;", "", text)
    text = re.sub(r"&[a-zA-Z]+;", "", text)
    text = re.sub(r"The post .* appeared first on .*\.", "", text)
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def to_4_sentences(text):
    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    return " ".join(sentences[:4])


def parse_pub_date(date_str):
    """Parse RFC 2822 (RSS) or ISO 8601 (Atom) date strings."""
    date_str = date_str.strip()
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        pass
    try:
        normalized = re.sub(r"(\.\d+)?Z$", "+00:00", date_str)
        return datetime.datetime.fromisoformat(normalized)
    except Exception:
        return None


def fetch_headlines(source, url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            xml = r.read().decode("utf-8", errors="ignore")

        # Try RSS <item> tags first, fall back to Atom <entry> tags
        items = re.findall(r"<item>(.*?)</item>", xml, re.DOTALL)
        is_atom = not items
        if is_atom:
            items = re.findall(r"<entry>(.*?)</entry>", xml, re.DOTALL)

        results = []
        now = datetime.datetime.now(datetime.timezone.utc)
        for item in items:
            title_m = re.search(
                r"<title><!\[CDATA\[(.*?)\]\]></title>|<title[^>]*>(.*?)</title>",
                item, re.DOTALL)
            if is_atom:
                link_m = re.search(
                    r'<link[^>]+rel=["\']alternate["\'][^>]+href=["\']([^"\']+)["\']'
                    r'|<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']alternate["\']'
                    r'|<link[^>]+href=["\']([^"\']+)["\'][^/]*/>',
                    item)
                desc_m = re.search(
                    r"<summary[^>]*><!\[CDATA\[(.*?)\]\]></summary>"
                    r"|<summary[^>]*>(.*?)</summary>",
                    item, re.DOTALL)
                date_m = re.search(
                    r"<published>(.*?)</published>|<updated>(.*?)</updated>", item)
            else:
                link_m = re.search(
                    r"<link>(.*?)</link>|<link\s[^>]*href=[\"'](.*?)[\"']",
                    item, re.DOTALL)
                desc_m = re.search(
                    r"<description><!\[CDATA\[(.*?)\]\]></description>"
                    r"|<description>(.*?)</description>",
                    item, re.DOTALL)
                date_m = re.search(r"<pubDate>(.*?)</pubDate>", item)

            if not title_m:
                continue
            t = next((g for g in title_m.groups() if g), "").strip()
            t = clean_text(t)
            if not t or len(t) <= 15:
                continue

            if date_m:
                try:
                    date_str = next((g for g in date_m.groups() if g), "")
                    dt = parse_pub_date(date_str)
                    if dt is None:
                        continue
                    if (now - dt).days > MAX_AGE_DAYS:
                        continue
                    pub = dt.strftime("%b %d, %Y %I:%M %p %Z")
                except Exception:
                    continue
            else:
                continue

            l = ""
            if link_m:
                l = next((g for g in link_m.groups() if g), "").strip()
                l = re.sub(r"\s+", "", l)

            d = ""
            if desc_m:
                raw = next((g for g in desc_m.groups() if g), "").strip()
                d = to_4_sentences(clean_text(raw))

            results.append((source, t, l, d, pub))
        return results[:10]
    except Exception as e:
        print(f"  Failed to fetch {source}: {e}")
        return []


def score(item):
    title = item[1]
    t = (title + " " + item[3]).lower()
    s = 0
    for w in BREAKING_WORDS:
        if w in t:
            s += 5
    for w in MARKETING_WORDS:
        if w in t:
            s += 3
    for w in AI_WORDS:
        if w in t:
            s += 1
    for w in LOW_VALUE_WORDS:
        if w in t:
            s -= 12
    for w in STORY_WORDS:
        if w in t:
            s -= 15
    # Penalty for numbered list-style tutorial titles ("7 Ways to...", "10 Best...")
    if re.match(r'^\d+\s+', title.strip()):
        title_low = title.lower()
        if any(x in title_low for x in [
                'way', 'tip', 'reason', 'tool', 'example',
                'step', 'tactic', 'best ', 'top ', 'trick']):
            s -= 12
    # Freshness bonus — newest articles float to top for Reel-worthy breaking news
    try:
        dt = parse_pub_date(item[4])
        if dt:
            age_hours = (datetime.datetime.now(datetime.timezone.utc) - dt).total_seconds() / 3600
            if age_hours <= 24:
                s += 10
            elif age_hours <= 48:
                s += 5
    except Exception:
        pass
    return s


def matches_topic(title, keywords):
    t = title.lower()
    return any(kw in t for kw in keywords)


def select_articles(pool, exclude_urls=None):
    if exclude_urls is None:
        exclude_urls = set()
    # Drop previously sent articles and anything below minimum quality score
    pool = [h for h in pool if h[2] not in exclude_urls and score(h) >= MIN_SCORE]

    selected = []
    used_indices = set()

    for topic_keywords in GUARANTEED_TOPICS:
        for i, h in enumerate(pool):
            if i not in used_indices and matches_topic(h[1], topic_keywords):
                selected.append(h)
                used_indices.add(i)
                break

    ai_count = sum(1 for h in selected if is_ai_article(h[1], h[3]))

    for i, h in enumerate(pool):
        if len(selected) >= MAX_ARTICLES:
            break
        if i not in used_indices and is_marketing_relevant(h[1], h[3]):
            if is_ai_article(h[1], h[3]):
                if ai_count < 2:
                    selected.append(h)
                    used_indices.add(i)
                    ai_count += 1
            else:
                selected.append(h)
                used_indices.add(i)

    return selected


def get_morning_urls(all_headlines):
    """Simulate what morning.py picks — fallback when GitHub API is unavailable."""
    by_score = sorted(all_headlines, key=score, reverse=True)
    picked = select_articles(by_score)
    return {h[2] for h in picked}


def main():
    date_str = datetime.date.today().strftime("%B %d, %Y")
    slot = "Evening"
    print(f"Fetching headlines for {date_str} ({slot} edition)...")

    all_headlines = []
    for source, url in FEEDS:
        headlines = fetch_headlines(source, url)
        print(f"  {source}: {len(headlines)} headlines")
        all_headlines.extend(headlines)

    print(f"  {len(all_headlines)} total articles within {MAX_AGE_DAYS} days")

    # Load cross-day + same-day dedup list from GitHub API
    sent_urls = load_sent_urls()
    if not sent_urls:
        # Fallback: simulate morning's picks to at least deduplicate same-day
        sent_urls = get_morning_urls(all_headlines)
        print(f"  Fallback: excluding {len(sent_urls)} simulated morning articles")
    else:
        print(f"  Excluding {len(sent_urls)} previously sent articles")

    # Evening: sort by most recently published
    def pub_key(item):
        try:
            dt = parse_pub_date(item[4])
            return dt if dt else datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
        except Exception:
            return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)

    all_headlines.sort(key=pub_key, reverse=True)

    selected = select_articles(all_headlines, exclude_urls=sent_urls)

    if not selected:
        print("No headlines fetched — aborting.")
        return

    lines = [f"DAILY MARKETING NEWS - {date_str} (Evening)", ""]
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

    print(f"\nSending {len(selected)} articles...")

    msg = MIMEText(body)
    msg["Subject"] = f"Daily Marketing News (Evening) - {date_str}"
    msg["From"] = GMAIL_USER
    msg["To"] = ", ".join(RECIPIENTS)

    with smtplib.SMTP("smtp.gmail.com", 587) as s:
        s.starttls()
        s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        s.sendmail(GMAIL_USER, RECIPIENTS, msg.as_string())

    print("Email sent to:", ", ".join(RECIPIENTS))

    # Persist sent URLs so next runs skip these articles
    save_sent_urls({h[2] for h in selected if h[2]})


if __name__ == "__main__":
    main()
