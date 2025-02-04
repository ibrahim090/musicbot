# بوت دسكورد للموسيقى

بوت دسكورد بسيط لتشغيل الموسيقى في القنوات الصوتية.

## المتطلبات

1. Python 3.8 أو أحدث
2. FFmpeg
3. توكن بوت دسكورد

## التثبيت المحلي

1. قم بتثبيت المتطلبات:
```bash
pip install -r requirements.txt
```

2. قم بتثبيت FFmpeg:
- لنظام Windows: قم بتحميله من [موقع FFmpeg الرسمي](https://ffmpeg.org/download.html) وأضفه إلى متغيرات النظام
- لنظام Linux: `sudo apt-get install ffmpeg`
- لنظام MacOS: `brew install ffmpeg`

3. أنشئ ملف `.env` وأضف توكن البوت:
```
DISCORD_TOKEN=your_token_here
```

## النشر على Railway

1. قم بإنشاء حساب على [Railway](https://railway.app/)
2. اربط حسابك على GitHub
3. انشئ مشروع جديد واختر "Deploy from GitHub repo"
4. أضف المتغيرات البيئية التالية:
   - `DISCORD_TOKEN`: توكن البوت الخاص بك

## الأوامر المتاحة

- `!join`: للانضمام إلى القناة الصوتية
- `!leave`: لمغادرة القناة الصوتية
- `!play [رابط]`: لتشغيل أغنية من رابط يوتيوب
- `!pause`: لإيقاف الأغنية مؤقتاً
- `!resume`: لاستئناف تشغيل الأغنية
- `!stop`: لإيقاف تشغيل الأغنية

## كيفية التشغيل محلياً

1. تأكد من إضافة توكن البوت في ملف `.env`
2. قم بتشغيل البوت:
```bash
python bot.py
``` 