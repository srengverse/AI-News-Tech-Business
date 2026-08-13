# AI Finance, Technology & Business News Bot

ប្រព័ន្ធប្រមូល សង្ខេប និងផ្សព្វផ្សាយព័ត៌មានអំពី **ហិរញ្ញវត្ថុ បច្ចេកវិទ្យា និងអាជីវកម្ម** ជាភាសាខ្មែរ។ ប្រព័ន្ធនេះប្រើ RSS feeds, Google Gemini, Supabase, Facebook Pages និង Telegram Channels ដើម្បីបង្កើត workflow ស្វ័យប្រវត្តិពីការទាញព័ត៌មានរហូតដល់ការបង្ហោះ។

## សមត្ថភាពសំខាន់

- តាមដានប្រភព RSS ចំនួន ១៦ ក្នុង ៣ ប្រភេទ៖ Finance, Technology និង Business។ ក្នុងនោះមានប្រភពក្នុងស្រុកកម្ពុជា ដូចជា NBC, Open Development Cambodia និង Khmer Times។
- ស្រង់រូបភាពពី RSS media, `og:image`, `twitter:image` ឬ HTML របស់អត្ថបទ។
- ប្រើ Google Gemini ដើម្បីបង្កើតចំណងជើង សេចក្តីសង្ខេប និងទស្សនៈវិភាគជាភាសាខ្មែរ។
- បង្កើត vertical video reel `1080x1920` ជាមួយ Khmer AI voice-over, poster visual និង branding របស់ project។ ប្រសិនបើ TTS ឬ ffmpeg មិនអាចប្រើបាន ប្រព័ន្ធនឹង fallback ទៅ poster workflow ចាស់។
- ផ្សព្វផ្សាយទៅ Facebook Page និង Telegram Channel។
- រក្សាទុកអត្ថបទដែលបានបង្ហោះក្នុង Supabase និងការពារការបង្ហោះស្ទួនតាម article ID និង fingerprint។
- មាន dashboard សម្រាប់មើលស្ថិតិ និងបញ្ជា scan ដោយដៃ។
- មាន retry/backoff, API-key rotation, circuit breaker, image cache និង environment validation។

> ព័ត៌មានទីផ្សារ និងអត្ថបទដែលសង្ខេបដោយ AI គួរត្រូវបានពិនិត្យជាមួយប្រភពដើម មុនពេលយកទៅប្រើសម្រាប់ការសម្រេចចិត្តហិរញ្ញវត្ថុ។

## ប្រភពព័ត៌មានលំនាំដើម

| ប្រភេទ | ប្រភព |
|---|---|
| Finance | CNBC Finance, Yahoo Finance, MarketWatch, NBC Cambodia News, NBC Cambodia Press, ODC Banking & Financial Services |
| Technology | TechCrunch, MIT Technology Review, Google AI Blog, ODC Cambodia Fintech, Khmer Times Technology |
| Business | CNBC Business, Entrepreneur, Forbes Business, Khmer Times Business, ODC Cambodia Economy |

ប្រភពអាចកែប្រែបាននៅក្នុង `NEWS_SOURCES` ក្នុង `news.py`។ ប្រព័ន្ធនឹងត្រួតពិនិត្យ keyword ដើម្បីបន្ថយអត្ថបទដែលមិនពាក់ព័ន្ធនឹង finance, technology ឬ business។ ប្រភពផ្លូវការរបស់ NBC ត្រូវបានរាយនៅលើ [ទំព័រ RSS/Social Media របស់ NBC][3]។ ប្រភព Khmer Times និង ODC ប្រើ category/tag RSS endpoints របស់គេហទំព័រផ្លូវការ។

## Tech Stack

- Python 3.10+
- AIOHTTP និង asyncio
- Google Gemini API (`google-genai`)
- Supabase PostgreSQL
- Feedparser និង BeautifulSoup4
- Pillow សម្រាប់ poster generation
- FFmpeg សម្រាប់ reel rendering និង audio/video muxing
- OpenAI Speech API សម្រាប់ Khmer voice-over

## ដំឡើង និងដំណើរការ

ត្រូវការ Python 3.10 ឬថ្មីជាងនេះ, Supabase project, Google Gemini API key, Facebook Page access token និង Telegram bot configuration។

```bash
git clone https://github.com/srengverse/AI-News-Tech-Business.git
cd AI-News-Tech-Business
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

បង្កើត `.env` នៅ root directory៖

```env
GEMINI_API_KEY=your_gemini_api_key_1,your_gemini_api_key_2
GEMINI_MODEL=gemini-2.0-flash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_service_role_key
FACEBOOK_ACCESS_TOKEN=your_facebook_page_access_token
FACEBOOK_PAGE_ID=your_facebook_page_id
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHANNEL_ID=your_telegram_channel_id
PORT=8080
DASHBOARD_HOST=127.0.0.1
DASHBOARD_TOKEN=replace_with_a_long_random_secret
REQUEST_TIMEOUT_SECONDS=15
MAX_IMAGE_BYTES=8388608
MAX_ARTICLE_BYTES=2097152
MAX_FEED_BYTES=4194304
MAX_REEL_BYTES=52428800
MEDIA_MODE=reel
OPENAI_API_KEY=your_openai_api_key
TTS_MODEL=gpt-4o-mini-tts
TTS_VOICE=alloy
FONT_PATH=Battambang-Bold.ttf
LOGO_PATH=logo.png
```

បន្ទាប់មក run៖

```bash
python3 news.py
```

Dashboard នឹងបើកតាម `http://localhost:8080`។ Reel mode ត្រូវការ `ffmpeg` នៅក្នុង system និង `OPENAI_API_KEY`។ `MEDIA_MODE=reel` នឹងព្យាយាមបង្កើត Khmer voice-over និង publish MP4 ទៅ Facebook Reels/Telegram video; បើមិនអាចបង្កើតបាន វានឹង fallback ទៅ poster ដោយស្វ័យប្រវត្តិ។ សម្រាប់ production គួររក្សា `DASHBOARD_HOST=127.0.0.1` ហើយដាក់ dashboard នៅពីក្រោយ reverse proxy/TLS។ ប្រសិនបើត្រូវ bind ទៅ network interface សាធារណៈ ត្រូវកំណត់ `DASHBOARD_TOKEN` ជា random secret វែង ហើយ endpoint manual trigger នឹងទាមទារ `X-Dashboard-Token`។ កុំ commit `.env` ឬ credentials ពិតទៅក្នុង Git repository។

## Database

ដំណើរការ SQL ក្នុង `SUPABASE_SCHEMA.sql` តាម Supabase SQL Editor មុនពេល run bot។ Schema រក្សាទុកអត្ថបទដែលបានបង្ហោះ និង retry queue សម្រាប់កំហុសដែលអាចកើតមាន។ Migration នឹងបន្ថែម `category` និង `link` ទៅ table ចាស់ដោយសុវត្ថិភាព ហើយបើក Row Level Security ដើម្បីបិទ anonymous/public database access។

## ឯកសារសំខាន់ៗ

| ឯកសារ | តួនាទី |
|---|---|
| `news.py` | Worker, RSS ingestion, AI summarization, poster/reel generation, Khmer voice-over និង publishing |
| `dashboard.html` | Live monitoring dashboard |
| `SUPABASE_SCHEMA.sql` | Database tables និង indexes |
| `requirements.txt` | Python dependencies |
| `Battambang-Bold.ttf` | Khmer font សម្រាប់ poster |
| `logo.png` | Project logo សម្រាប់ poster និង reel |
| `tests/test_project.py` | Regression tests សម្រាប់ source, security និង media workflow |

## License

MIT License។

## Source

Project នេះត្រូវបានកែសម្រួលពី [`srengverse/bot_News`][1] សម្រាប់ប្រើជាប្រភពព័ត៌មាន Finance, Technology និង Business នៅក្នុង [`srengverse/AI-News-Tech-Business`][2]។

*Author: Manus AI*

[1]: https://github.com/srengverse/bot_News "Original bot_News repository"
[2]: https://github.com/srengverse/AI-News-Tech-Business "AI-News-Tech-Business repository"
[3]: https://www.nbc.gov.kh/english/about_the_bank/social_network.php "National Bank of Cambodia RSS feeds"
