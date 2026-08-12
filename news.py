# -*- coding: utf-8 -*-
# news.py — AI Finance, Technology & Business News Bot (Supabase, Facebook & Telegram)
# Version: 17.0 - Finance, Technology & Business Edition
# Last Updated: 2026-08-12

import os
import asyncio
import json
import hashlib
import logging
import html
import io
import re
import sys
import time
from datetime import datetime, timedelta
from urllib.parse import urljoin
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
load_dotenv()

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
DAILY_REPORT_TIME = os.getenv("DAILY_REPORT_TIME", "22:00")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
ICT = pytz.timezone('Asia/Phnom_Penh')
FONT_PATH = os.getenv("FONT_PATH", "Battambang-Bold.ttf")
LOGO_PATH = os.getenv("LOGO_PATH", "logo.png")

# Global Event for Manual Trigger
scan_event = asyncio.Event()

# --- Cache Settings ---
CACHE_DIR = "image_cache"
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
        "SUPABASE_KEY": SUPABASE_KEY,
        "FACEBOOK_ACCESS_TOKEN": FB_ACCESS_TOKEN,
        "FACEBOOK_PAGE_ID": FB_PAGE_ID
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        logging.error(f" Critical: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)

    if not os.path.exists(FONT_PATH):
        logging.warning(f" WARNING: '{FONT_PATH}' not found! Text rendering might fail.")

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
            logging.error(" All Gemini API keys exhausted. Waiting 60s...")
            time.sleep(60)
            self.failed_keys.clear()
            return self.keys[0]

        if self.current_index not in available:
            self.current_index = available[0]
        return self.keys[self.current_index]

    def mark_failed(self):
        self.failed_keys[self.current_index] = time.time() + 600 # 10 min lockout
        logging.warning(f" API Key {self.current_index} rate limited. Rotating...")

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
    normalized = f"{title.lower().strip()} {summary.lower().strip()[:150]}"
    return hashlib.md5(normalized.encode()).hexdigest()

def is_relevant_business_news(article: dict) -> bool:
    """Reject feed items that are clearly outside finance, technology or business."""
    keywords = [
        'finance', 'financial', 'market', 'markets', 'stock', 'stocks', 'economy',
        'bank', 'banking', 'investment', 'investor', 'business', 'company',
        'startup', 'technology', 'tech', 'software', 'artificial intelligence',
        ' ai ', 'semiconductor', 'cybersecurity', 'cloud', 'digital', 'bitcoin',
        'blockchain', 'economics', 'trade', 'ipo', 'revenue', 'profit'
    ]
    text = f" {article.get('title', '')} {article.get('summary', '')} ".lower()
    return any(k in text for k in keywords)

# ===========================  SERVICES ===========================
class ImageService:
    @staticmethod
    async def download(url: str) -> Optional[bytes]:
        if not validate_url(url): return None
        cache_path = os.path.join(CACHE_DIR, f"{hashlib.md5(url.encode()).hexdigest()}.jpg")

        if os.path.exists(cache_path):
            mtime = datetime.fromtimestamp(os.path.getmtime(cache_path))
            if datetime.now() - mtime < timedelta(hours=CACHE_EXPIRY_HOURS):
                with open(cache_path, 'rb') as f: return f.read()

        try:
            async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as session:
                async with session.get(url, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        with open(cache_path, 'wb') as f: f.write(data)
                        return data
        except: pass
        return None

    @staticmethod
    async def generate_poster(image_bytes, title, source, is_neg=False, cat="default"):
        target = (1200, 800)
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
                img = Image.new('RGBA', target, theme["bg"] + (255,))
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
            if os.path.exists(LOGO_PATH):
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
    async def is_duplicate(aid: str, fingerprint: str) -> bool:
        try:
            # Check ID
            res = await asyncio.to_thread(lambda: supabase.table('posted_articles').select('id').eq('id', aid).execute())
            if res.data: return True
            # Check Fingerprint
            res = await asyncio.to_thread(lambda: supabase.table('posted_articles').select('id').eq('fingerprint', fingerprint).limit(1).execute())
            return bool(res.data)
        except: return False

    @staticmethod
    async def save_post(aid, title, finger, fb, tg, src, category, link):
        try:
            await asyncio.to_thread(lambda: supabase.table('posted_articles').insert({
                "id": aid, "title": title, "fingerprint": finger,
                "facebook": fb, "telegram": tg, "source": src,
                "category": category, "link": link
            }).execute())
        except Exception as e: logging.error(f" DB Save Failed: {e}")

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
            if data:
                article.update(data)
                return article
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                gemini_manager.mark_failed()
            raise
        return None

# ===========================  SOCIAL POSTING ===========================
async def post_facebook(art: dict, img: Optional[bytes]) -> bool:
    if not FB_ACCESS_TOKEN or not FB_PAGE_ID: return False
    msg = f"{art.get('title_kh', '')}\n\n{art.get('summary_kh', '')}\n\n{art.get('insight', '')}\n\nអានលម្អិត: {art['link']}\n\n{art.get('hashtags', '')} #aitbnews"
    try:
        async with aiohttp.ClientSession() as s:
            if img:
                url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
                d = FormData()
                d.add_field('access_token', FB_ACCESS_TOKEN)
                d.add_field('message', msg)
                d.add_field('source', img, filename='n.jpg', content_type='image/jpeg')
                async with s.post(url, data=d, timeout=30) as r:
                    if 'id' in await r.json(): return True

            url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
            d = FormData()
            d.add_field('access_token', FB_ACCESS_TOKEN)
            d.add_field('message', msg)
            d.add_field('link', art['link'])
            async with s.post(url, data=d, timeout=20) as r:
                return 'id' in await r.json()
    except: return False

async def post_telegram(art: dict, img: Optional[bytes]) -> bool:
    if not TG_BOT_TOKEN or not TG_CHANNEL_ID: return False
    msg = f"{art.get('title_kh', '')}\n\n{art.get('summary_kh', '')}\n\n{art.get('insight', '')}\n\nRead: {art['link']}\n\n{art.get('hashtags', '')}"
    try:
        async with aiohttp.ClientSession() as s:
            if img:
                url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto"
                d = FormData()
                d.add_field('chat_id', TG_CHANNEL_ID)
                d.add_field('caption', msg)
                d.add_field('photo', img, filename='n.jpg')
                async with s.post(url, data=d) as r:
                    if (await r.json()).get('ok'): return True

            url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
            async with s.post(url, json={'chat_id': TG_CHANNEL_ID, 'text': msg}) as r:
                return (await r.json()).get('ok')
    except: return False

# ===========================  NEWS SOURCES ===========================
NEWS_SOURCES = {
    "finance": [
        {"name": "CNBC Finance", "url": "https://www.cnbc.com/id/10000664/device/rss/rss.html"},
        {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/news/rssindex"},
        {"name": "MarketWatch", "url": "https://feeds.marketwatch.com/marketwatch/topstories/"}
    ],
    "technology": [
        {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
        {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/feed/"},
        {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss/"}
    ],
    "business": [
        {"name": "CNBC Business", "url": "https://www.cnbc.com/id/10001147/device/rss/rss.html"},
        {"name": "Entrepreneur", "url": "https://www.entrepreneur.com/latest.rss"},
        {"name": "Forbes Business", "url": "https://www.forbes.com/business/feed/"}
    ]
}

# ===========================  MAIN WORKER ===========================
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

            # Memory Management
            if len(recent_cache) > 1000: recent_cache.clear()

            posted = 0
            for cat, sources in NEWS_SOURCES.items():
                if posted >= limit: break
                for src in sources:
                    if posted >= limit: break
                    if not circuit_breaker.can_call(src['name']): continue

                    try:
                        feed = await asyncio.to_thread(feedparser.parse, src['url'])
                        for e in feed.entries[:5]:
                            if posted >= limit: break
                            link = getattr(e, 'link', None)
                            if not link: continue

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
                            if hasattr(e, 'media_content'):
                                img_url = e.media_content[0].get('url')
                            if not img_url and e.get('summary'):
                                img_tag = BeautifulSoup(e.summary, 'html.parser').find('img')
                                if img_tag: img_url = urljoin(link, img_tag.get('src'))

                            # HTML Fallback
                            if not img_url:
                                try:
                                    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as s:
                                        async with s.get(link, timeout=10) as r:
                                            if r.status == 200:
                                                soup = BeautifulSoup(await r.text(), 'html.parser')
                                                meta = soup.find('meta', property='og:image') or soup.find('meta', name='twitter:image')
                                                if meta: img_url = urljoin(link, meta.get('content'))
                                except: pass

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
async def index(r): return web.FileResponse('dashboard.html')

@routes.get('/api/stats')
async def stats(r):
    try:
        now = datetime.now(ICT)
        today = now.replace(hour=0, minute=0, second=0).isoformat()
        week = (now - timedelta(days=7)).isoformat()

        # Optimized Queries
        res_all = await asyncio.to_thread(lambda: supabase.table('posted_articles').select('id', count='exact').execute())
        res_today = await asyncio.to_thread(lambda: supabase.table('posted_articles').select('*').gte('posted_at', today).execute())
        res_week = await asyncio.to_thread(lambda: supabase.table('posted_articles').select('id', count='exact').gte('posted_at', week).execute())

        today_data = res_today.data or []
        return web.json_response({
            "total_all": res_all.count or 0,
            "total_today": len(today_data),
            "total_week": res_week.count or 0,
            "success_count": sum(1 for x in today_data if x.get('facebook') or x.get('telegram')),
            "recent_posts": today_data[:10],
            "category_counts": {
                category: sum(1 for item in today_data if item.get('category') == category)
                for category in ('finance', 'technology', 'business')
            },
            "timestamp": now.isoformat()
        })
    except Exception as e: return web.json_response({"error": str(e)}, status=500)

@routes.post('/api/trigger')
async def trigger(r):
    scan_event.set()
    return web.json_response({"status": "triggered"})

async def main():
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 8080)))
    await site.start()
    logging.info(f" Dashboard running on port {os.getenv('PORT', 8080)}")

    # Run Workers
    await asyncio.gather(worker(), asyncio.sleep(0)) # Add retry_worker here if needed

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: pass
