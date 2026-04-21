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
    # SEO / Search
    ("Search Engine Land",   "https://searchengineland.com/feed"),
    ("Search Engine Journal","https://www.searchenginejournal.com/feed/"),
    ("SE Roundtable",        "https://www.seroundtable.com/feed.xml"),
    ("Moz Blog",             "https://moz.com/blog/feed"),
    ("Ahrefs Blog",          "https://ahrefs.com/blog/feed/"),
    ("Backlinko",            "https://backlinko.com/blog/feed"),
    # Paid Ads
    ("WordStream",           "https://www.wordstream.com/blog/feed"),
    ("PPC Hero",             "https://www.ppchero.com/feed/"),
    # Social Media
    ("Social Media Examiner","https://www.socialmediaexaminer.com/feed/"),
    ("Social Media Today",   "https://www.socialmediatoday.com/rss/"),
    ("Sprout Social",        "https://sproutsocial.com/insights/feed/"),
    # General Marketing
    ("Marketing Brew",       "https://www.marketingbrew.com/feed.xml"),
    ("HubSpot Marketing",    "https://blog.hubspot.com/marketing/rss.xml"),
    ("MarTech",              "https://martech.org/feed/"),
    ("AdWeek",               "https://www.adweek.com/feed/"),
    # Web / CMS
    ("WP Tavern",            "https://wptavern.com/feed"),
    ("Smashing Magazine",    "https://www.smashingmagazine.com/feed/"),
    ("Web Designer Depot",   "https://webdesignerdepot.com/feed/"),
    # Local SEO
    ("BrightLocal",          "https://www.brightlocal.com/blog/feed/"),
    ("Sterling Sky",         "https://sterlingsky.ca/feed/"),
    ("Near Media",           "https://www.nearmedia.co/feed/"),
    # Tools
    ("Semrush Blog",         "https://www.semrush.com/blog/feed/"),
    ("Neil Patel",           "https://neilpatel.com/blog/feed/"),
]

BREAKING_WORDS = [
    "algorithm update", "core update", "broad core", "manual action", "penalty",
    "rolling out", "rolls out", "new feature", "breaking", "major change",
    "policy change", "ban", "deindex", "spam update", "ranking update",
    "serp change", "leaked", "ranking factor", "search ranking change",
    "helpful content", "google confirms", "google says", "google warns",
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
    "introduction to", "getting started",
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

MAX_ARTICLES = 13
MAX_AGE_DAYS = 3


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


def fetch_headlines(source, url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            xml = r.read().decode("utf-8", errors="ignore")
        items = re.findall(r"<item>(.*?)</item>", xml, re.DOTALL)
        results = []
        now = datetime.datetime.now(datetime.timezone.utc)
        for item in items:
            title_m = re.search(r"<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>", item)
            link_m  = re.search(r"<link>(.*?)</link>|<link\s[^>]*href=[\"'](.*?)[\"']", item, re.DOTALL)
            desc_m  = re.search(r"<description><!\[CDATA\[(.*?)\]\]></description>|<description>(.*?)</description>", item, re.DOTALL)
            date_m  = re.search(r"<pubDate>(.*?)</pubDate>", item)
            if not title_m:
                continue
            t = (title_m.group(1) or title_m.group(2) or "").strip()
            if not t or len(t) <= 15:
                continue
            # Age filter — skip articles with no date or older than MAX_AGE_DAYS
            if date_m:
                try:
                    dt = parsedate_to_datetime(date_m.group(1).strip())
                    if (now - dt).days > MAX_AGE_DAYS:
                        continue
                    pub = dt.strftime("%b %d, %Y %I:%M %p %Z")
                except Exception:
                    continue  # unparseable date = skip
            else:
                continue  # no date = skip
            l = ""
            if link_m:
                l = (link_m.group(1) or link_m.group(2) or "").strip()
                l = re.sub(r"\s+", "", l)
            d = ""
            if desc_m:
                raw = (desc_m.group(1) or desc_m.group(2) or "").strip()
                d = to_4_sentences(clean_text(raw))
            results.append((source, t, l, d, pub))
        return results[:10]
    except Exception as e:
        print(f"  Failed to fetch {source}: {e}")
        return []


def score(item):
    t = (item[1] + " " + item[3]).lower()
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
            s -= 5
    for w in STORY_WORDS:
        if w in t:
            s -= 8
    return s


def matches_topic(title, keywords):
    t = title.lower()
    return any(kw in t for kw in keywords)


def select_articles(pool):
    selected = []
    used_indices = set()

    # Guaranteed slots first
    for topic_keywords in GUARANTEED_TOPICS:
        for i, h in enumerate(pool):
            if i not in used_indices and matches_topic(h[1], topic_keywords):
                selected.append(h)
                used_indices.add(i)
                break

    ai_count = sum(1 for h in selected if is_ai_article(h[1], h[3]))

    # Fill remaining with marketing-relevant, AI capped at 2
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

    # Fallback: any relevant article
    for i, h in enumerate(pool):
        if len(selected) >= MAX_ARTICLES:
            break
        if i not in used_indices and is_marketing_relevant(h[1], h[3]):
            selected.append(h)
            used_indices.add(i)

    return selected


def main():
    date_str = datetime.date.today().strftime("%B %d, %Y")
    slot = "Morning"
    print(f"Fetching headlines for {date_str} ({slot} edition)...")

    all_headlines = []
    for source, url in FEEDS:
        headlines = fetch_headlines(source, url)
        print(f"  {source}: {len(headlines)} headlines")
        all_headlines.extend(headlines)

    print(f"  {len(all_headlines)} total articles within {MAX_AGE_DAYS} days")

    # Morning: sort by score (most important news first)
    all_headlines.sort(key=score, reverse=True)

    selected = select_articles(all_headlines)

    if not selected:
        print("No headlines fetched — aborting.")
        return

    lines = [f"DAILY MARKETING NEWS - {date_str} (Morning)", ""]
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
    msg["Subject"] = f"Daily Marketing News (Morning) - {date_str}"
    msg["From"] = GMAIL_USER
    msg["To"] = ", ".join(RECIPIENTS)

    with smtplib.SMTP("smtp.gmail.com", 587) as s:
        s.starttls()
        s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        s.sendmail(GMAIL_USER, RECIPIENTS, msg.as_string())

    print("Email sent to:", ", ".join(RECIPIENTS))


if __name__ == "__main__":
    main()
