# Discord Music Bot

بوت ديسكورد للموسيقى يدعم تشغيل المقاطع من YouTube وSpotify.

## المميزات

- تشغيل مقاطع من YouTube (روابط مباشرة أو بحث)
- دعم روابط Spotify (مقاطع وقوائم تشغيل)
- أوامر التحكم الأساسية (تشغيل، إيقاف مؤقت، استئناف، إيقاف)
- عرض معلومات المقطع (العنوان، المدة، الصورة المصغرة)
- دعم قوائم التشغيل من Spotify

## المتطلبات

- Python 3.8 أو أحدث
- FFmpeg
- حساب مطور في Discord
- حساب مطور في Spotify

## التثبيت

1. قم بتثبيت المتطلبات:
```bash
pip install -r requirements.txt
```

2. قم بإنشاء ملف `.env` وأضف المتغيرات التالية:
```env
DISCORD_TOKEN=your_discord_token
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
```

3. قم بتشغيل البوت:
```bash
python src/bot.py
```

## الأوامر

- `!play [رابط/بحث]` - تشغيل مقطع من YouTube أو Spotify
- `!pause` - إيقاف مؤقت للتشغيل
- `!resume` - استئناف التشغيل
- `!stop` - إيقاف التشغيل
- `!leave` - مغادرة القناة الصوتية

## الترخيص

MIT 