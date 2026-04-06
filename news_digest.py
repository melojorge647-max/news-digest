import smtplib
import datetime
import urllib.request
import re
import os
from email.mime.text import MIMEText
from email.utils import parsedate_to_datetime

GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
RECIPIENTS = ["melojorge647@gmail.com", "jorge@jmelomedia.com", "info@jmelomedia.com", "camrynalvares03@gmail.com"]

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
    ("Web Designer Depot",   "https://webdesignerdepot.com/feed/"),
    ("WordStream",           "https://www.wordstream.com/blog/feed"),
    ("Neil Patel",           "https://neilpatel.com/blog/feed/"),
    # Local SEO for service businesses
    ("BrightLocal",          "https://www.brightlocal.com/blog/feed/"),
    ("Sterling Sky",         "https://sterlingsky.ca/feed/"),
    ("Whitespark",           "https://whitespark.ca/blog/feed/"),
    ("Near Media",           "https://www.nearmedia.co/feed/"),
    # Creator economy / platform news
    ("Social Media Today",   "https://www.socialmediatoday.com/rss.xml"),
    ("The Verge",            "https://www.theverge.com/rss/index.xml"),
]

# Highest priority — breaking news, algorithm changes, major announcements (+5 each)
BREAKING_WORDS = [
    # Google search
    "algorithm update", "core update", "broad core", "manual action", "penalty",
    "rolling out", "rolls out", "new feature", "breaking", "major change",
    "policy change", "ban", "deindex", "spam update", "ranking update",
    "serp change", "leaked", "ranking factor", "search ranking change",
    "helpful content", "google confirms", "google says", "google warns",
    # Meta / Facebook / Instagram
    "meta announces", "meta confirms", "meta update", "meta launches",
    "facebook announces", "facebook update", "facebook algorithm", "facebook launches",
    "instagram announces", "instagram launches", "instagram update", "instagram algorithm",
    "reels update", "feed update", "feed algorithm",
    # LinkedIn
    "linkedin announces", "linkedin launches", "linkedin update", "linkedin algorithm",
    # TikTok
    "tiktok announces", "tiktok launches", "tiktok update", "tiktok algorithm",
    "tiktok ban", "tiktok changes",
    # YouTube
    "youtube announces", "youtube launches", "youtube update", "youtube algorithm",
    "youtube monetization", "youtube changes",
    # X / Twitter
    "x announces", "twitter announces", "x update", "twitter update",
    "x algorithm", "twitter algorithm", "x launches",
    # Snapchat / Pinterest / Threads
    "snapchat announces", "snapchat update", "pinterest announces", "pinterest update",
    "threads announces", "threads update", "threads algorithm",
    # Other search engines
    "bing update", "bing announces", "bing algorithm", "bing changes",
    "search engine update", "search update",
    # Ads platforms
    "google ads update", "meta ads update", "ad policy change", "ads announcement",
    "performance max update", "smart bidding update",
    # Creator economy / monetization
    "paying creators", "creator fund", "creator monetization", "creator economy",
    "bonus program", "revenue share", "creator program", "creator payout",
    "ad revenue sharing", "platform pays", "monetize creators",
    # CEOs / executives
    "zuckerberg", "adam mosseri", "ryan roslansky", "sundar pichai", "satya nadella",
    "ceo says", "ceo announces", "ceo confirms",
    # Local SEO breaking
    "google business profile update", "gbp update", "map pack change", "local pack update",
    "google maps update", "local search update",
]

# Marketing/SEO priority keywords — scored highly (+3 each)
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
    # Local SEO for service businesses
    "gbp", "map pack", "local pack", "local search", "local ranking",
    "google maps ranking", "plumber", "roofer", "hvac", "electrician", "contractor",
    "home service", "service area", "review management", "citation", "local citation",
    "near me", "local 3-pack", "local business", "google reviews",
]

# AI keywords — capped at 2 articles per digest (+1 each)
AI_WORDS = [
    "artificial intelligence", "chatgpt", "openai", "gemini", "claude",
    "llm", "large language model", "ai overview", "ai search", "generative ai",
    "perplexity", "copilot", "gpt", "machine learning",
]

# Generic fluff — penalized heavily (-5 each)
LOW_VALUE_WORDS = [
    "how to", "guide to", "tutorial", "tips for", "best practices",
    "checklist", "step by step", "beginners guide", "101", "complete guide",
    "ultimate guide", "everything you need to know", "what is", "explained",
    "introduction to", "getting started",
]

# Story/opinion content — buried unless nothing else is available (-8 each)
STORY_WORDS = [
    "opinion", "my experience", "case study", "interview with", "podcast",
    "webinar", "roundup", "weekly recap", "monthly recap", "predictions for",
    "lessons learned", "retrospective", "thought leadership", "personal story",
    "i tested", "we tested", "here's what", "here is what",
]

# Must contain at least one of these to be included
REQUIRED_KEYWORDS = [
    "seo", "search", "google", "bing", "ads", "ppc", "paid",
    "marketing", "meta", "facebook", "instagram", "tiktok", "linkedin",
    "youtube", "social media", "content", "website", "web", "digital",
    "local", "rank", "traffic", "campaign", "algorithm", "serp", "keyword",
    "backlink", "analytics", "conversion", "email marketing", "wordpress",
    "wix", "squarespace", "webflow", "landing page", "funnel", "lead",
    "ai", "chatgpt", "openai", "automation", "crm", "shopify", "ecommerce",
]

# Guaranteed slots — at least 1 article from each group
GUARANTEED_TOPICS = [
    ["wordpress", "wix", "squarespace", "webflow", "lovable", "website builder",
     "web design", "web development", "website design", "page speed", "core web vitals", "cms"],
    ["instagram", "facebook", "meta ads", "reels", "social media"],
    ["google business profile", "gbp", "map pack", "local pack", "local seo",
     "local search", "local ranking", "plumber", "roofer", "hvac", "electrician",
     "home service", "contractor", "near me", "local 3-pack", "local citation",
     "google reviews", "service area business"],
]


def is_marketing_relevant(title, summary):
    combined = (title + " " + summary).lower()
    return any(kw in combined for kw in REQUIRED_KEYWORDS)


def is_ai_article(title, summary):
    combined = (title + " " + summary).lower()
    return any(kw in combined for kw in AI_WORDS)


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
                results.append((source, t, l, d, pub, date_m.group(1).strip() if date_m else ""))
        return results[:10]
    except Exception as e:
        print(f"  Failed to fetch {source}: {e}")
        return []


def score(item):
    t = (item[1] + " " + item[3]).lower()
    s = 0
    for w in BREAKING_WORDS:
        if w in t:
            s += 5   # top priority: breaking news / platform changes
    for w in MARKETING_WORDS:
        if w in t:
            s += 3   # high priority: marketing/seo specific
    for w in AI_WORDS:
        if w in t:
            s += 1   # low priority: ai articles
    for w in LOW_VALUE_WORDS:
        if w in t:
            s -= 5   # penalize generic how-to / guide content
    for w in STORY_WORDS:
        if w in t:
            s -= 8   # heavily bury opinion/story/recap content
    return s


def matches_topic(title, keywords):
    t = title.lower()
    return any(kw in t for kw in keywords)


def main():
    date_str = datetime.date.today().strftime("%B %d, %Y")
    offset = int(os.environ.get("ARTICLE_OFFSET", "0"))
    slot = "Evening" if offset >= 10 else "Morning"
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

    ai_count = sum(1 for h in selected if is_ai_article(h[1], h[3]))

    # Fill remaining slots — marketing relevant, cap AI at 2
    for i, h in enumerate(all_headlines):
        if len(selected) >= 12:
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

    # Fall back: any relevant non-AI articles
    for i, h in enumerate(all_headlines):
        if len(selected) >= 12:
            break
        if i not in used_indices and is_marketing_relevant(h[1], h[3]) and not is_ai_article(h[1], h[3]):
            selected.append(h)
            used_indices.add(i)

    if not selected:
        print("No headlines fetched — aborting.")
        return

    lines = [f"DAILY MARKETING NEWS - {date_str}", ""]
    for i, (source, title, link, summary, pub, _raw_date) in enumerate(selected, 1):
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
