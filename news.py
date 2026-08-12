# -*- coding: utf-8 -*-
# news.py — AI Finance, Technology & Business News Bot (Supabase, Facebook & Telegram)
# Version: 17.0 - Finance, Technology & Business Edition
# Last Updated: 2026-08-12

import os
import asyncio
import json
import hashlib
import hmac
import ipaddress
import logging
import io
import re
import socket
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Tuple, Set, Any, Callable
from dataclasses import dataclass
from functools import wraps
from collections import defaultdict

# Third-party imports
try:
    import pytz
    from dotenv import load_dotenv
    import aiohttp
    import feedparser
    from bs4 import BeautifulSoup
    from google import genai
    from google.genai import types
    from aiohttp import web, FormData
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance
    from supabase import create_client, Client
except ImportError as e:
    print(f" Missing dependency: {e}")
    print(" Please run: pip install -r requirements.txt")
    exit(1)

# ===========================  CONFIGURATION ===========================
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

# --- Credentials ---
def get_env_list(key: str, default: str = "") -> List[str]:
    val = os.getenv(key, default)
    return [k.strip() for k in val.split(",") if k.strip()]

GEMINI_API_KEYS = get_env_list("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
FB_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
FB_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
TG_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

# --- Admin Settings ---
def env_int(key: str, default: int, minimum: int, maximum: int) -> int:
    try:
        return max(minimum, min(maximum, int(os.getenv(key, str(default)))))
    except (TypeError, ValueError):
        return default


def env_float(key: str, default: float, minimum: float, maximum: float) -> float:
    try:
        return max(minimum, min(maximum, float(os.getenv(key, str(default)))))
    except (TypeError, ValueError):
        return default


DAILY_REPORT_TIME = os.getenv("DAILY_REPORT_TIME", "22:00")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
ICT = pytz.timezone('Asia/Phnom_Penh')
FONT_PATH = Path(os.getenv("FONT_PATH", str(BASE_DIR / "Battambang-Bold.ttf"))).expanduser()
LOGO_PATH = Path(os.getenv("LOGO_PATH", str(BASE_DIR / "logo.png"))).expanduser()
DASHBOARD_TOKEN = os.getenv("DASHBOARD_TOKEN")
DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "127.0.0.1")
REQUEST_TIMEOUT_SECONDS = env_float("REQUEST_TIMEOUT_SECONDS", 15.0, 3.0, 60.0)
MAX_IMAGE_BYTES = env_int("MAX_IMAGE_BYTES", 8 * 1024 * 1024, 64 * 1024, 20 * 1024 * 1024)
MAX_ARTICLE_BYTES = env_int("MAX_ARTICLE_BYTES", 2 * 1024 * 1024, 64 * 1024, 10 * 1024 * 1024)
MAX_FEED_BYTES = env_int("MAX_FEED_BYTES", 4 * 1024 * 1024, 64 * 1024, 10 * 1024 * 1024)

# Global Event for Manual Trigger
scan_event = asyncio.Event()

# --- Cache Settings ---
CACHE_DIR = str(BASE_DIR / os.getenv("CACHE_DIR", "image_cache"))
CACHE_MAX_SIZE_MB = 100
CACHE_EXPIRY_HOURS = 24

# --- Poster Themes ---
def parse_color(env_val, default):
    if not env_val: return default
    try:
        parts = [int(x.strip()) for x in env_val.split(",")]
        return tuple(parts)
    except: return default

POSTER_THEMES = {
    "finance": {
        "bg": parse_color(os.getenv("THEME_FINANCE_BG"), (20, 55, 80)),
        "accent": parse_color(os.getenv("THEME_FINANCE_ACCENT"), (80, 210, 190, 40))
    },
    "technology": {
        "bg": parse_color(os.getenv("THEME_TECHNOLOGY_BG"), (45, 20, 80)),
        "accent": parse_color(os.getenv("THEME_TECHNOLOGY_ACCENT"), (180, 120, 255, 35))
    },
    "business": {
        "bg": parse_color(os.getenv("THEME_BUSINESS_BG"), (80, 45, 15)),
        "accent": parse_color(os.getenv("THEME_BUSINESS_ACCENT"), (255, 190, 80, 35))
    },
    "breaking": {
        "bg": parse_color(os.getenv("THEME_BREAKING_BG"), (100, 0, 0)),
        "accent": parse_color(os.getenv("THEME_BREAKING_ACCENT"), (255, 255, 255, 50))
    },
    "default": {
        "bg": parse_color(os.getenv("THEME_DEFAULT_BG"), (30, 40, 60)),
        "accent": parse_color(os.getenv("THEME_DEFAULT_ACCENT"), (255, 255, 255, 10))
    }
}

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# ===========================  SYSTEM CHECKS ===========================
def check_environment():
    required = {
        "GEMINI_API_KEY": GEMINI_API_KEYS,
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_KEY": SUPABASE_KEY
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        logging.error(f" Critical: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)

    if not os.path.exists(FONT_PATH):
        logging.warning(f" WARNING: '{FONT_PATH}' not found! Text rendering might fail.")

    if not FB_ACCESS_TOKEN or not FB_PAGE_ID:
        logging.warning("Facebook publishing is disabled; Telegram-only mode is active")
    if not TG_BOT_TOKEN or not TG_CHANNEL_ID:
        logging.warning("Telegram publishing is disabled; Facebook-only mode is active")
    if not DASHBOARD_TOKEN:
        logging.warning("DASHBOARD_TOKEN is not configured; manual trigger endpoint is unauthenticated")
    logging.info(f" Environment verified. Gemini Keys: {len(GEMINI_API_KEYS)}")

check_environment()

# ===========================  INITIALIZATION ===========================
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logging.info(" Supabase Connection Established")
except Exception as e:
    logging.critical(f" Supabase Initialization Failed: {e}")
    sys.exit(1)

os.makedirs(CACHE_DIR, exist_ok=True)


def cleanup_cache() -> None:
    """Remove expired cache entries and enforce the configured cache size limit."""
    try:
        files = [entry for entry in os.scandir(CACHE_DIR) if entry.is_file()]
        cutoff = time.time() - CACHE_EXPIRY_HOURS * 3600
        for entry in files:
            if entry.stat().st_mtime < cutoff:
                os.remove(entry.path)
        files = [entry for entry in os.scandir(CACHE_DIR) if entry.is_file()]
        total = sum(entry.stat().st_size for entry in files)
        limit = CACHE_MAX_SIZE_MB * 1024 * 1024
        for entry in sorted(files, key=lambda item: item.stat().st_mtime):
            if total <= limit:
                break
            size = entry.stat().st_size
            os.remove(entry.path)
            total -= size
    except OSError as exc:
        logging.warning("Cache cleanup failed: %s", exc)

# ===========================  CORE UTILITIES ===========================
def retry_with_backoff(max_retries: int = 3, base_delay: float = 2.0):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1: raise
                    wait = delay * (2 ** attempt)
                    logging.warning(f" {func.__name__} attempt {attempt+1} failed. Retrying in {wait}s...")
                    await asyncio.sleep(wait)
        return wrapper
    return decorator

class GeminiManager:
    def __init__(self, keys: List[str]):
        self.keys = keys
        self.current_index = 0
        self.failed_keys = {} # key_index -> reset_time

    def get_key(self) -> str:
        now = time.time()
        # Clean up expired failed keys (wait 10 mins)
        self.failed_keys = {k: t for k, t in self.failed_keys.items() if now < t}

        available = [i for i in range(len(self.keys)) if i not in self.failed_keys]
        if not available:
            raise RuntimeError("All Gemini API keys are temporarily unavailable")

        if self.current_index not in available:
            self.current_index = available[0]
        return self.keys[self.current_index]

    def mark_failed(self):
        failed_index = self.current_index
        self.failed_keys[failed_index] = time.time() + 600  # 10-minute lockout
        if self.keys:
            self.current_index = (failed_index + 1) % len(self.keys)
        logging.warning(f" API Key {failed_index} rate limited. Rotating...")

gemini_manager = GeminiManager(GEMINI_API_KEYS)

class CircuitBreaker:
    def __init__(self, threshold: int = 5, timeout: int = 600):
        self.threshold = threshold
        self.timeout = timeout
        self.failures = defaultdict(int)
        self.open_until = defaultdict(float)

    def can_call(self, key: str) -> bool:
        if time.time() < self.open_until[key]: return False
        return True

    def record_failure(self, key: str):
        self.failures[key] += 1
        if self.failures[key] >= self.threshold:
            self.open_until[key] = time.time() + self.timeout
            logging.error(f" Circuit Breaker OPEN for {key}")

    def record_success(self, key: str):
        self.failures[key] = 0
        self.open_until[key] = 0

circuit_breaker = CircuitBreaker()

# ===========================  DATA MODELS ===========================
@dataclass
class FailedPost:
    article_id: str
    article_data: Dict[str, Any]
    image_bytes: Optional[bytes]
    attempts: int
    last_attempt: datetime
    error_message: str

def validate_url(url: Optional[str]) -> bool:
    return bool(url and isinstance(url, str) and url.startswith(('http://', 'https://')))


def is_safe_public_url(url: Optional[str]) -> bool:
    """Allow public HTTP(S) URLs while blocking localhost/private-network SSRF targets."""
    if not validate_url(url):
        return False
    try:
        parsed = urlparse(url)
        if parsed.username or parsed.password or not parsed.hostname:
            return False
        hostname = parsed.hostname.rstrip('.').lower()
        if hostname in {'localhost', 'localhost.localdomain'} or hostname.endswith('.local'):
            return False
        addresses = {item[4][0] for item in socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == 'https' else 80), type=socket.SOCK_STREAM)}
        return all(not (ip := ipaddress.ip_address(address)).is_private
                   and not ip.is_loopback and not ip.is_link_local
                   and not ip.is_multicast and not ip.is_reserved for address in addresses)
    except (OSError, ValueError):
        return False

def safe_json_parse(text: str) -> Optional[dict]:
    try:
        return json.loads(text)
    except:
        try:
            cleaned = re.sub(r'```(?:json)?\s*|\s*```', '', text).strip()
            return json.loads(cleaned)
        except:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try: return json.loads(match.group(0))
                except: pass
    return None

def create_article_fingerprint(title: str, summary: str) -> str:
    normalized = f"{str(title).lower().strip()} {str(summary).lower().strip()[:150]}"
    # Keep MD5 for backward compatibility with fingerprints already stored in Supabase.
    return hashlib.md5(normalized.encode()).hexdigest()

def is_relevant_business_news(article: dict) -> bool:
    """Reject feed items that are clearly outside finance, technology or business."""
    keywords = [
        'finance', 'financial', 'market', 'markets', 'stock', 'stocks', 'economy',
        'bank', 'banking', 'investment', 'investor', 'business', 'company',
        'startup', 'technology', 'tech', 'software', 'artificial intelligence',
        ' ai ', 'semiconductor', 'cybersecurity', 'cloud', 'digital', 'bitcoin',
        'blockchain', 'economics', 'trade', 'ipo', 'revenue', 'profit',
        'ហិរញ្ញ', 'បច្ចេក', 'អាជីវ', 'ធនាគារ', 'វិនិយោគ', 'ទីផ្សារ', 'សេដ្ឋកិច្ច',
        'ក្រុមហ៊ុន', 'ឌីជីថល', 'បញ្ញាសិប្បនិម្មិត'
    ]
    text = f" {article.get('title', '')} {article.get('summary', '')} ".lower()
    return any(k in text for k in keywords)

# ===========================  SERVICES ===========================
class ImageService:
    @staticmethod
    async def download(url: str) -> Optional[bytes]:
        if not is_safe_public_url(url):
            logging.warning("Blocked unsafe image URL")
            return None
        cache_path = os.path.join(CACHE_DIR, f"{hashlib.sha256(url.encode()).hexdigest()}.img")

        if os.path.exists(cache_path):
            mtime = datetime.fromtimestamp(os.path.getmtime(cache_path))
            if datetime.now() - mtime < timedelta(hours=CACHE_EXPIRY_HOURS):
                try:
                    with Image.open(cache_path) as cached:
                        cached.verify()
                    with open(cache_path, 'rb') as f:
                        return f.read()
                except (OSError, ValueError):
                    try:
                        os.remove(cache_path)
                    except OSError:
                        pass

        try:
            timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)
            async with aiohttp.ClientSession(headers={'User-Agent': 'AI-News-Tech-Business/1.0'}, timeout=timeout) as session:
                async with session.get(url, allow_redirects=True) as resp:
                    if resp.status != 200 or not is_safe_public_url(str(resp.url)):
                        return None
                    content_type = resp.headers.get('Content-Type', '').lower()
                    if content_type and not (content_type.startswith('image/') or content_type == 'application/octet-stream'):
                        return None
                    if resp.content_length and resp.content_length > MAX_IMAGE_BYTES:
                        return None
                    data = await resp.content.read(MAX_IMAGE_BYTES + 1)
                    if len(data) > MAX_IMAGE_BYTES:
                        return None
                    with open(cache_path, 'wb') as f:
                        f.write(data)
                    return data
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as exc:
            logging.warning("Image download failed: %s", exc)
        return None

    @staticmethod
    async def generate_poster(image_bytes, title, source, is_neg=False, cat="default"):
        target = (1200, 800)
        title = str(title or "News")[:240]
        source = str(source or "Unknown")[:120]
        try:
            if image_bytes:
                img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
                # Smart Crop
                aspect = img.width / img.height
                t_aspect = target[0] / target[1]
                if aspect > t_aspect:
                    img = img.resize((int(target[1] * aspect), target[1]), Image.Resampling.LANCZOS)
                    left = (img.width - target[0]) // 2
                    img = img.crop((left, 0, left + target[0], target[1]))
                else:
                    img = img.resize((target[0], int(target[0] / aspect)), Image.Resampling.LANCZOS)
                    top = (img.height - target[1]) // 2
                    img = img.crop((0, top, target[0], target[1]))
            else:
                theme = POSTER_THEMES.get(cat, POSTER_THEMES["default"])
                img = Image.new('RGBA', target, tuple(theme["bg"][:3]) + (255,))
                draw = ImageDraw.Draw(img)
                for y in range(800):
                    draw.line([(0, y), (1200, y)], fill=(0, 0, 0, int(40 * y / 800)))
                for x in range(0, 1200, 50):
                    for y in range(0, 800, 50):
                        draw.ellipse([x, y, x+4, y+4], fill=theme["accent"])

            img = ImageEnhance.Brightness(img).enhance(0.8)
            overlay = Image.new('RGBA', target, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            for y in range(350, 800):
                draw.line([(0, y), (1200, y)], fill=(0, 0, 0, int(200 * ((y-350)/450)**1.5)))

            out = Image.alpha_composite(img, overlay)
            draw = ImageDraw.Draw(out)

            def get_f(s):
                try: return ImageFont.truetype(FONT_PATH, s)
                except: return ImageFont.load_default()

            # Badge
            badge = "BREAKING NEWS" if is_neg else "FINANCE • TECH • BUSINESS"
            b_clr = (200, 0, 0) if is_neg else (0, 80, 200)
            draw.rectangle([50, 520, 300, 565], fill=b_clr)
            draw.text((65, 525), badge, font=get_f(24), fill="white")

            # Title wrapping
            lines, cur = [], ""
            f_t = get_f(52)
            for w in title.split():
                if draw.textbbox((0,0), cur + w, font=f_t)[2] < 1100: cur += w + " "
                else: lines.append(cur.strip()); cur = w + " "
            lines.append(cur.strip())

            y_off = 585
            for l in lines[:3]:
                draw.text((50, y_off), l, font=f_t, fill="white", stroke_width=2, stroke_fill="black")
                y_off += 75

            # Logo & Meta
            if LOGO_PATH.exists():
                logo = Image.open(LOGO_PATH).convert("RGBA").resize((130, 130), Image.Resampling.LANCZOS)
                out.paste(logo, (1030, 40), logo)

            draw.text((50, y_off + 20), f"{source} • {datetime.now(ICT):%d %b %Y}", font=get_f(28), fill=(200, 200, 200))

            buf = io.BytesIO()
            out.convert("RGB").save(buf, format='JPEG', quality=90)
            return buf.getvalue()
        except Exception as e:
            logging.error(f" Poster Generation Failed: {e}")
            return None

class DatabaseService:
    @staticmethod
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    async def is_duplicate(aid: str, fingerprint: str) -> bool:
        # A database error must stop processing this article; returning False could cause duplicates.
        res = await asyncio.to_thread(lambda: supabase.table('posted_articles').select('id').eq('id', aid).limit(1).execute())
        if res.data:
            return True
        res = await asyncio.to_thread(lambda: supabase.table('posted_articles').select('id').eq('fingerprint', fingerprint).limit(1).execute())
        return bool(res.data)

    @staticmethod
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    async def save_post(aid, title, finger, fb, tg, src, category, link) -> bool:
        await asyncio.to_thread(lambda: supabase.table('posted_articles').insert({
            "id": aid, "title": title, "fingerprint": finger,
            "facebook": fb, "telegram": tg, "source": src,
            "category": category, "link": link
        }).execute())
        return True

class AIService:
    @staticmethod
    @retry_with_backoff(max_retries=2)
    async def summarize(article: dict) -> Optional[dict]:
        try:
            key = gemini_manager.get_key()
            client = genai.Client(api_key=key)
            prompt = f"""
            Article: {article.get('title', '')}
            Summary: {article.get('summary', '')}
            Source: {article.get('source', '')}

            Role: Expert Senior Journalist.
            Task: Provide a high-level, sophisticated Khmer summary for a finance, technology or business audience.
            Style: Professional, fluid paragraph, elegant tone. No bullets.
            Output JSON:
            {{
                "title_kh": "Professional Khmer title",
                "summary_kh": "High-level summary paragraph (2-3 sentences)",
                "insight": "Analytical perspective in Khmer, including business or market implications",
                "sentiment": "Positive/Neutral/Negative",
                "hashtags": "#Finance #Technology #Business #Khmer"
            }}
            """
            resp = await client.aio.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type='application/json'),
            )

            text = getattr(resp, 'text', '')
            if not text and hasattr(resp, 'candidates'):
                text = "".join([p.text for p in resp.candidates[0].content.parts if hasattr(p, 'text')])

            data = safe_json_parse(text)
            if not isinstance(data, dict):
                logging.warning("Gemini returned invalid JSON")
                return None
            required = ('title_kh', 'summary_kh', 'insight', 'sentiment', 'hashtags')
            if any(not str(data.get(field, '')).strip() for field in required):
                logging.warning("Gemini response is missing required fields")
                return None
            data['sentiment'] = str(data['sentiment']).strip().title()
            if data['sentiment'] not in {'Positive', 'Neutral', 'Negative'}:
                data['sentiment'] = 'Neutral'
            for field in required:
                data[field] = str(data[field]).strip()[:4000]
            article.update(data)
            return article
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                gemini_manager.mark_failed()
            raise
        return None

# ===========================  SOCIAL POSTING ===========================
async def post_facebook(art: dict, img: Optional[bytes]) -> bool:
    if not FB_ACCESS_TOKEN or not FB_PAGE_ID or not is_safe_public_url(art.get('link')):
        return False
    msg = f"{art.get('title_kh', '')}\n\n{art.get('summary_kh', '')}\n\n{art.get('insight', '')}\n\nអានលម្អិត: {art['link']}\n\n{art.get('hashtags', '')} #aitbnews"[:63000]
    try:
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)
        async with aiohttp.ClientSession(timeout=timeout) as s:
            if img:
                url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
                d = FormData()
                d.add_field('access_token', FB_ACCESS_TOKEN)
                d.add_field('message', msg)
                d.add_field('source', img, filename='n.jpg', content_type='image/jpeg')
                async with s.post(url, data=d, timeout=30) as r:
                    payload = await r.json(content_type=None)
                    if r.status < 300 and 'id' in payload:
                        return True

            url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
            d = FormData()
            d.add_field('access_token', FB_ACCESS_TOKEN)
            d.add_field('message', msg)
            d.add_field('link', art['link'])
            async with s.post(url, data=d) as r:
                payload = await r.json(content_type=None)
                return r.status < 300 and 'id' in payload
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as exc:
        logging.warning("Facebook publish failed: %s", exc)
        return False

async def post_telegram(art: dict, img: Optional[bytes]) -> bool:
    if not TG_BOT_TOKEN or not TG_CHANNEL_ID or not is_safe_public_url(art.get('link')):
        return False
    msg = f"{art.get('title_kh', '')}\n\n{art.get('summary_kh', '')}\n\n{art.get('insight', '')}\n\nRead: {art['link']}\n\n{art.get('hashtags', '')}"[:4096]
    try:
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)
        async with aiohttp.ClientSession(timeout=timeout) as s:
            if img:
                url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto"
                d = FormData()
                d.add_field('chat_id', TG_CHANNEL_ID)
                d.add_field('caption', msg)
                d.add_field('photo', img, filename='n.jpg')
                async with s.post(url, data=d) as r:
                    payload = await r.json(content_type=None)
                    if r.status < 300 and payload.get('ok'):
                        return True

            url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
            async with s.post(url, json={'chat_id': TG_CHANNEL_ID, 'text': msg}) as r:
                payload = await r.json(content_type=None)
                return r.status < 300 and payload.get('ok', False)
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as exc:
        logging.warning("Telegram publish failed: %s", exc)
        return False

# ===========================  NEWS SOURCES ===========================
NEWS_SOURCES = {
    "finance": [
        {"name": "CNBC Finance", "url": "https://www.cnbc.com/id/10000664/device/rss/rss.html"},
        {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/news/rssindex"},
        {"name": "MarketWatch", "url": "https://feeds.marketwatch.com/marketwatch/topstories/"},
        {"name": "NBC Cambodia News", "url": "http://www.nbc.org.kh/rss/rss_feed.php?feed=news"},
        {"name": "NBC Cambodia Press", "url": "http://www.nbc.org.kh/rss/rss_feed.php?feed=press"},
        {"name": "ODC Banking & Financial Services", "url": "https://opendevelopmentcambodia.net/en/category/economy-and-commerce/banking-and-financial-services/feed/"}
    ],
    "technology": [
        {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
        {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/feed/"},
        {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss/"},
        {"name": "ODC Cambodia Fintech", "url": "https://opendevelopmentcambodia.net/en/tag/financial-technology-fintech/feed/"},
        {"name": "Khmer Times Technology", "url": "https://www.khmertimeskh.com/tag/technology/feed/"}
    ],
    "business": [
        {"name": "CNBC Business", "url": "https://www.cnbc.com/id/10001147/device/rss/rss.html"},
        {"name": "Entrepreneur", "url": "https://www.entrepreneur.com/latest.rss"},
        {"name": "Forbes Business", "url": "https://www.forbes.com/business/feed/"},
        {"name": "Khmer Times Business", "url": "https://www.khmertimeskh.com/category/business/feed/"},
        {"name": "ODC Cambodia Economy", "url": "https://opendevelopmentcambodia.net/en/category/economy-and-commerce/feed/"}
    ]
}

# ===========================  MAIN WORKER ===========================
async def fetch_feed(url: str):
    """Fetch a bounded RSS document with async timeout before parsing it."""
    if not is_safe_public_url(url):
        raise ValueError("Unsafe feed URL")
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)
    async with aiohttp.ClientSession(headers={'User-Agent': 'AI-News-Tech-Business/1.0'}, timeout=timeout) as session:
        async with session.get(url, allow_redirects=True) as response:
            if response.status != 200 or not is_safe_public_url(str(response.url)):
                raise RuntimeError(f"Feed returned HTTP {response.status}")
            if response.content_length and response.content_length > MAX_FEED_BYTES:
                raise ValueError("Feed exceeds configured size limit")
            payload = await response.content.read(MAX_FEED_BYTES + 1)
            if len(payload) > MAX_FEED_BYTES:
                raise ValueError("Feed exceeds configured size limit")
            return feedparser.parse(payload)


async def fetch_article_image_url(link: str) -> Optional[str]:
    if not is_safe_public_url(link):
        return None
    try:
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)
        async with aiohttp.ClientSession(headers={'User-Agent': 'AI-News-Tech-Business/1.0'}, timeout=timeout) as session:
            async with session.get(link, allow_redirects=True) as response:
                if response.status != 200 or not is_safe_public_url(str(response.url)):
                    return None
                content_type = response.headers.get('Content-Type', '').lower()
                if content_type and 'html' not in content_type:
                    return None
                if response.content_length and response.content_length > MAX_ARTICLE_BYTES:
                    return None
                payload = await response.content.read(MAX_ARTICLE_BYTES + 1)
                if len(payload) > MAX_ARTICLE_BYTES:
                    return None
                soup = BeautifulSoup(payload, 'html.parser')
                meta = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'twitter:image'})
                return urljoin(link, meta.get('content')) if meta and meta.get('content') else None
    except (aiohttp.ClientError, asyncio.TimeoutError, OSError, ValueError):
        return None


async def worker():
    logging.info(" Starting Main Worker Loop...")
    recent_cache = set()

    while True:
        try:
            h = datetime.now(ICT).hour
            # Dynamic interval: Night (1hr), Peak (10m), Normal (20m)
            interval, limit = (3600, 1) if 0 <= h < 5 else ((600, 2) if 5 <= h < 9 or 11 <= h < 14 or 17 <= h < 20 else (1200, 2))

            # Manual trigger support
            try: await asyncio.wait_for(scan_event.wait(), timeout=interval)
            except asyncio.TimeoutError: pass
            scan_event.clear()

            # Memory and disk management
            if len(recent_cache) > 1000:
                recent_cache.clear()
            cleanup_cache()

            posted = 0
            for cat, sources in NEWS_SOURCES.items():
                if posted >= limit: break
                for src in sources:
                    if posted >= limit: break
                    if not circuit_breaker.can_call(src['name']): continue

                    try:
                        feed = await fetch_feed(src['url'])
                        for e in feed.entries[:5]:
                            if posted >= limit: break
                            link = getattr(e, 'link', None)
                            if not link: continue

                            if not is_safe_public_url(link):
                                continue
                            # Keep MD5 for backward compatibility with existing posted article IDs.
                            aid = hashlib.md5(link.encode()).hexdigest()
                            if aid in recent_cache: continue

                            raw = {
                                "title": getattr(e, 'title', 'News'),
                                "link": link,
                                "summary": BeautifulSoup(e.get('summary', ''), "html.parser").get_text()[:1500],
                                "source": src['name'], "category": cat
                            }

                            if not is_relevant_business_news(raw): continue

                            finger = create_article_fingerprint(raw['title'], raw['summary'])
                            if await DatabaseService.is_duplicate(aid, finger):
                                recent_cache.add(aid)
                                continue

                            # Image Extraction
                            img_url = None
                            media_content = e.get('media_content') or []
                            if media_content and isinstance(media_content, list):
                                img_url = media_content[0].get('url')
                            if not img_url and e.get('summary'):
                                img_tag = BeautifulSoup(e.summary, 'html.parser').find('img')
                                if img_tag: img_url = urljoin(link, img_tag.get('src'))

                            # HTML Fallback
                            if not img_url:
                                img_url = await fetch_article_image_url(link)

                            # Process
                            final = await AIService.summarize(raw)
                            if not final: continue

                            img_data = await ImageService.download(img_url) if img_url else None
                            poster = await ImageService.generate_poster(img_data, final['title_kh'], final['source'], final.get('sentiment')=='Negative', cat)

                            fb_ok = await post_facebook(final, poster or img_data)
                            tg_ok = await post_telegram(final, poster or img_data)

                            if fb_ok or tg_ok:
                                await DatabaseService.save_post(
                                    aid, final['title'], finger, fb_ok, tg_ok,
                                    src['name'], cat, final['link']
                                )
                                recent_cache.add(aid)
                                posted += 1
                                circuit_breaker.record_success(src['name'])
                                await asyncio.sleep(30) # Rate limit protection
                            else:
                                circuit_breaker.record_failure(src['name'])

                    except Exception as e:
                        logging.error(f" Source Error ({src['name']}): {e}")
                        circuit_breaker.record_failure(src['name'])

        except Exception as e:
            logging.error(f" Worker Loop Error: {e}")
            await asyncio.sleep(60)

# ===========================  WEB DASHBOARD ===========================
routes = web.RouteTableDef()

@routes.get('/')
async def index(r):
    return web.FileResponse(BASE_DIR / 'dashboard.html')

@routes.get('/api/stats')
async def stats(r):
    try:
        now = datetime.now(ICT)
        today = now.replace(hour=0, minute=0, second=0).isoformat()
        week = (now - timedelta(days=7)).isoformat()

        # Optimized Queries
        post_fields = 'id,title,posted_at,facebook,telegram,source,category,link'
        res_all = await asyncio.to_thread(lambda: supabase.table('posted_articles').select('id', count='exact').execute())
        res_today = await asyncio.to_thread(lambda: supabase.table('posted_articles').select('facebook,telegram,category').gte('posted_at', today).execute())
        res_recent = await asyncio.to_thread(lambda: supabase.table('posted_articles').select(post_fields).gte('posted_at', week).order('posted_at', desc=True).limit(10).execute())
        res_week = await asyncio.to_thread(lambda: supabase.table('posted_articles').select('id', count='exact').gte('posted_at', week).execute())

        today_data = res_today.data or []
        recent_data = res_recent.data or []
        return web.json_response({
            "total_all": res_all.count or 0,
            "total_today": len(today_data),
            "total_week": res_week.count or 0,
            "success_count": sum(1 for x in today_data if x.get('facebook') or x.get('telegram')),
            "recent_posts": recent_data,
            "category_counts": {
                category: sum(1 for item in today_data if item.get('category') == category)
                for category in ('finance', 'technology', 'business')
            },
            "timestamp": now.isoformat()
        })
    except Exception:
        logging.exception("Dashboard stats query failed")
        return web.json_response({"error": "Unable to load dashboard statistics"}, status=500)

@routes.post('/api/trigger')
async def trigger(r):
    if DASHBOARD_TOKEN:
        provided = r.headers.get('X-Dashboard-Token', '')
        if not hmac.compare_digest(provided, DASHBOARD_TOKEN):
            return web.json_response({'error': 'Unauthorized'}, status=401)
    scan_event.set()
    return web.json_response({"status": "triggered"})

async def main():
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, DASHBOARD_HOST, int(os.getenv("PORT", 8080)))
    await site.start()
    logging.info(f" Dashboard running on port {os.getenv('PORT', 8080)}")

    # Run Workers
    await asyncio.gather(worker(), asyncio.sleep(0)) # Add retry_worker here if needed

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: pass
