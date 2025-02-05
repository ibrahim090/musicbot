# Discord Music Bot

بوت ديسكورد للموسيقى يدعم تشغيل المقاطع من YouTube وSpotify.

## المميزات

- تشغيل مقاطع من YouTube (روابط مباشرة أو بحث)
- دعم روابط Spotify (مقاطع وقوائم تشغيل)
- أوامر التحكم الأساسية (تشغيل، إيقاف مؤقت، استئناف، إيقاف)
- عرض معلومات المقطع (العنوان، المدة، الصورة المصغرة)
- دعم قوائم التشغيل من Spotify

## المتطلبات

- Python 3.11 أو أحدث
- FFmpeg
- حساب مطور في Discord
- حساب مطور في Spotify

## التثبيت

1. قم بإنشاء بيئة Python افتراضية:
```bash
python -m venv venv
source venv/bin/activate  # على Linux/macOS
venv\Scripts\activate     # على Windows
```

2. قم بتثبيت المتطلبات:
```bash
pip install -r requirements.txt
```

3. قم بإنشاء ملف `.env` وأضف المتغيرات التالية:
```env
DISCORD_TOKEN=your_discord_token
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
```

4. قم بتشغيل البوت:
```bash
python src/bot.py
```

## الأوامر

- `!play [رابط/بحث]` - تشغيل مقطع من YouTube أو Spotify
- `!pause` - إيقاف مؤقت للتشغيل
- `!resume` - استئناف التشغيل
- `!stop` - إيقاف التشغيل
- `!leave` - مغادرة القناة الصوتية

## هيكل المشروع

```
.
├── src/
│   ├── __init__.py
│   └── bot.py
├── utils/
│   ├── __init__.py
│   ├── spotify_handler.py
│   └── youtube_handler.py
├── config/
│   ├── __init__.py
│   └── config.py
├── .env
├── .gitignore
├── README.md
├── requirements.txt
└── setup.py
```

## الترخيص

MIT 