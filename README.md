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
- Gemini TTS API (`gemini-3.1-flash-tts-preview`) សម្រាប់ Khmer voice-over

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
GEMINI_TTS_MODEL=gemini-3.1-flash-tts-preview
TTS_VOICE=Kore
FONT_PATH=Battambang-Bold.ttf
LOGO_PATH=logo.png
```

បន្ទាប់មក run៖

```bash
python3 news.py
```

Dashboard នឹងបើកតាម `http://localhost:8080`។ Reel mode ត្រូវការ `ffmpeg` នៅក្នុង system និង `GEMINI_API_KEY`។ `MEDIA_MODE=reel` នឹងព្យាយាមបង្កើត Khmer voice-over និង publish MP4 ទៅ Facebook Reels/Telegram video; បើមិនអាចបង្កើតបាន វានឹង fallback ទៅ poster ដោយស្វ័យប្រវត្តិ។ សម្រាប់ production គួររក្សា `DASHBOARD_HOST=127.0.0.1` ហើយដាក់ dashboard នៅពីក្រោយ reverse proxy/TLS។ ប្រសិនបើត្រូវ bind ទៅ network interface សាធារណៈ ត្រូវកំណត់ `DASHBOARD_TOKEN` ជា random secret វែង ហើយ endpoint manual trigger នឹងទាមទារ `X-Dashboard-Token`។ កុំ commit `.env` ឬ credentials ពិតទៅក្នុង Git repository។

## Render.com Deployment

Project នេះមាន `Dockerfile`, `render.yaml` និង `.dockerignore` សម្រាប់ deploy ទៅ Render។ Blueprint ប្រើ **Web Service តែមួយ** ដែល run ទាំង dashboard និង RSS worker ក្នុង process ដូចគ្នា ដើម្បីកុំឲ្យមាន worker ពីរបង្ហោះព័ត៌មានស្ទួន។ Render នឹង inject `PORT` ដោយស្វ័យប្រវត្តិ ហើយ `DASHBOARD_HOST=0.0.0.0` ត្រូវបានកំណត់ក្នុង `render.yaml` សម្រាប់ health check និង public dashboard។

ក្នុង Render Dashboard ជ្រើស **New > Blueprint**, ភ្ជាប់ repository `srengverse/AI-News-Tech-Business` និងជ្រើស branch `main`។ Render នឹងអាន `render.yaml` ហើយបង្កើត service ដោយស្វ័យប្រវត្តិ។ បំពេញ secret environment variables ដែលមាន `sync: false` ដោយផ្ទាល់ក្នុង Render: `GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHANNEL_ID`, `DASHBOARD_TOKEN` និង Facebook credentials ប្រសិនបើត្រូវការ Facebook publishing។ កុំ commit `.env` ឬ credentials ទៅ GitHub។

Health check ប្រើ `GET /`។ Dashboard នឹងមាននៅ URL ដែល Render ផ្ដល់ឲ្យ ហើយ manual trigger ត្រូវប្រើ header `X-Dashboard-Token` ប្រសិនបើ `DASHBOARD_TOKEN` ត្រូវបានកំណត់។ Render Free instance អាច sleep និងមិនសមស្របសម្រាប់ background news worker ដែលត្រូវរត់ជាប់ជានិច្ច; គួរប្រើ instance ដែលមិន sleep សម្រាប់ production និងពិនិត្យ logs បន្ទាប់ពី deploy។

## Dashboard User Guide

Dashboard គឺជា web interface សម្រាប់តាមដានស្ថានភាព news worker និងស្ថិតិអត្ថបទដែលបានរក្សាទុកក្នុង Supabase។ នៅ local វាបើកតាម `http://127.0.0.1:8080`។ នៅ Render សូមបើក URL ដែល Render ផ្ដល់ឲ្យ។ Dashboard អាចបង្ហាញចំនួនអត្ថបទសរុប, ចំនួនអត្ថបទថ្ងៃនេះ, ចំនួនអត្ថបទក្នុង ៧ ថ្ងៃចុងក្រោយ, publishing success count, category counts និង recent posts។

បន្ទាប់ពីចូល Dashboard អ្នកអាចចុច **Refresh** ដើម្បីទាញស្ថិតិថ្មីពី server ឬចុច **Run Scan Now** ដើម្បីកំណត់ worker ឲ្យចាប់ផ្តើមស្កេន RSS មុនពេលវដ្តបន្ទាប់។ ប៊ូតុង manual scan មិនបង្ហាញ secret ក្នុង browser ទេ; ប្រសិនបើ `DASHBOARD_TOKEN` ត្រូវបានកំណត់ សូមប្រើ API example ខាងក្រោមសម្រាប់ manual trigger ពី command line។

### Dashboard Security

សម្រាប់ local development អាចទុក `DASHBOARD_HOST=127.0.0.1`។ សម្រាប់ Render ត្រូវប្រើ `DASHBOARD_HOST=0.0.0.0` ដើម្បីឲ្យ platform health check និង browser access បាន។ ក្នុង production ត្រូវកំណត់ `DASHBOARD_TOKEN` ជា random secret វែង ហើយដាក់ Dashboard នៅពីក្រោយ HTTPS។ Endpoint `/api/stats` គឺសម្រាប់អានស្ថិតិ ខណៈ `/api/trigger` គឺជាការបញ្ជាឲ្យ worker ស្កេន RSS ដូច្នេះកុំបើកវាជាសាធារណៈដោយគ្មាន token។

## Dashboard API Documentation

Base URL គឺជា `http://127.0.0.1:8080` ក្នុង local ឬ Render service URL ក្នុង production។ API ប្រើ JSON ហើយមិនមាន public API versioning នៅពេលនេះ។ Response errors មិនបញ្ចេញ internal exception details ដើម្បីការពារ operational information។

| Method | Endpoint | Authentication | Purpose |
|---|---|---|---|
| `GET` | `/` | None | បើក Dashboard HTML |
| `GET` | `/api/stats` | None | ទាញស្ថិតិ និង recent posts |
| `POST` | `/api/trigger` | `X-Dashboard-Token` ប្រសិនបើបានកំណត់ | កំណត់ manual RSS scan |

### `GET /api/stats`

Endpoint នេះទាញស្ថិតិពី `posted_articles` ក្នុង Supabase។ ឧទាហរណ៍ request៖

```bash
curl -sS https://YOUR-RENDER-SERVICE.onrender.com/api/stats
```

Response ជោគជ័យមានទម្រង់ប្រហាក់ប្រហែលនេះ៖

```json
{
  "total_all": 42,
  "total_today": 5,
  "total_week": 19,
  "success_count": 5,
  "recent_posts": [
    {
      "id": "...",
      "title": "Article title",
      "posted_at": "2026-08-13T08:00:00+00:00",
      "facebook": false,
      "telegram": true,
      "source": "Khmer Times Business",
      "category": "business",
      "link": "https://example.com/article"
    }
  ],
  "category_counts": {
    "finance": 2,
    "technology": 2,
    "business": 1
  },
  "timestamp": "2026-08-13T15:00:00+07:00"
}
```

`total_all` គឺចំនួន records ទាំងអស់, `total_today` គឺចំនួន records ចាប់ពីម៉ោង 00:00 តាម Asia/Phnom Penh, `total_week` គឺចំនួនក្នុង ៧ ថ្ងៃចុងក្រោយ និង `success_count` គឺចំនួនអត្ថបទថ្ងៃនេះដែលបានបង្ហោះទៅ Facebook ឬ Telegram យ៉ាងហោចណាស់មួយ channel។ `category_counts` រាប់ Finance, Technology និង Business សម្រាប់ថ្ងៃនេះ។ `recent_posts` ត្រឡប់តែ ១០ records ចុងក្រោយ ដើម្បីកាត់បន្ថយ payload។

ប្រសិនបើ Supabase query បរាជ័យ endpoint នឹងត្រឡប់៖

```json
{
  "error": "Unable to load dashboard statistics"
}
```

ជាមួយ HTTP status `500`។

### `POST /api/trigger`

Endpoint នេះកំណត់ internal event ឲ្យ worker ចាប់ផ្តើម scan cycle។ វាមិនរង់ចាំឲ្យ RSS processing បញ្ចប់ទេ ដូច្នេះ response `triggered` មានន័យថា scan ត្រូវបានកំណត់ឲ្យដំណើរការ មិនមែនមានន័យថាការបង្ហោះបានបញ្ចប់ទេ។

ប្រសិនបើ `DASHBOARD_TOKEN` ត្រូវបានកំណត់៖

```bash
curl -sS -X POST \
  -H "X-Dashboard-Token: ${DASHBOARD_TOKEN}" \
  https://YOUR-RENDER-SERVICE.onrender.com/api/trigger
```

Response ជោគជ័យ៖

```json
{"status":"triggered"}
```

បើ token ខុស ឬបាត់ នឹងទទួល៖

```json
{"error":"Unauthorized"}
```

ជាមួយ HTTP status `401`។ ប្រសិនបើ `DASHBOARD_TOKEN` មិនបានកំណត់ endpoint នេះមិនទាមទារ token ប៉ុន្តែវា **មិនសុវត្ថិភាពសម្រាប់ public deployment** ទេ; ត្រូវកំណត់ token មុន deploy production។

### Health Check និង Troubleshooting

Render ប្រើ `GET /` ជា health check។ ប្រសិនបើ service បើកមិនបាន សូមពិនិត្យថា `DASHBOARD_HOST=0.0.0.0`, `PORT` មិនត្រូវបាន hard-code ជំនួស Render port, និង Docker container ចាប់ផ្តើមដោយ `python news.py`។ ប្រសិនបើ Dashboard បើកបាន ប៉ុន្តែ `/api/stats` ត្រឡប់ `500`, សូមពិនិត្យ `SUPABASE_URL`, `SUPABASE_KEY`, schema migration និង RLS settings។ ប្រសិនបើ `/api/trigger` ត្រឡប់ `401`, សូមពិនិត្យ header `X-Dashboard-Token` និងតម្លៃ `DASHBOARD_TOKEN` ក្នុង service environment។

## Database

ដំណើរការ SQL ក្នុង `SUPABASE_SCHEMA.sql` តាម Supabase SQL Editor មុនពេល run bot។ Schema រក្សាទុកអត្ថបទដែលបានបង្ហោះ និង retry queue សម្រាប់កំហុសដែលអាចកើតមាន។ Migration នឹងបន្ថែម `category` និង `link` ទៅ table ចាស់ដោយសុវត្ថិភាព ហើយបើក Row Level Security ដើម្បីបិទ anonymous/public database access។

## ឯកសារសំខាន់ៗ

| ឯកសារ | តួនាទី |
|---|---|
| `news.py` | Worker, RSS ingestion, Gemini summarization/TTS, poster/reel generation, Khmer voice-over និង publishing |
| `dashboard.html` | Live monitoring dashboard |
| `SUPABASE_SCHEMA.sql` | Database tables និង indexes |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Render production container with FFmpeg |
| `render.yaml` | Render Blueprint និង environment variable placeholders |
| `.dockerignore` | ការពារ secrets/cache/demo artifacts ពេល build image |
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
