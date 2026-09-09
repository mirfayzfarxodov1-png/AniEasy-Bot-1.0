# AniEasy Bot 1.0

Production-oriented Telegram anime content management bot in Uzbek, built with Python, aiogram 3, SQLAlchemy and PostgreSQL/SQLite.

## Xususiyatlar
- Admin upload-session: videolar ketma-ket yuboriladi va qism raqami avtomatik beriladi.
- Caption orqali qism raqamini aniqlash va kerak bo‘lsa qo‘lda kiritish.
- Telegram `file_id` saqlanadi; videolar serverga ko‘chirib olinmaydi.
- Anime, qismlar, sevimlilar, davom ettirish, qidiruv, statistika.
- Adminlar `.env` orqali boshqariladi.
- SQLite development, PostgreSQL production.
- FSM, repository/service arxitekturasi, rate limit, logging, global error handling.
- Docker va docker-compose.
- Migration uchun Alembic.

## O‘rnatish
Python 3.11+ tavsiya qilinadi.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env
```

`.env` ichida `BOT_TOKEN`, `ADMIN_IDS` va production uchun `DATABASE_URL` ni kiriting.

> Xavfsizlik: bot tokenini GitHub'ga yozmang. Agar token GitHub, chat yoki boshqa joyda oshkor bo‘lgan bo‘lsa, BotFather orqali darhol almashtiring.

## Ishga tushirish

```bash
alembic upgrade head
python -m app.main
```

## Docker

```bash
docker compose up -d --build
```

Migration:
```bash
docker compose exec bot alembic upgrade head
```

## Production
- PostgreSQL ishlating.
- `.env` ni serverda saqlang.
- `docker compose restart` yoki restart policy orqali avtomatik qayta ishga tushirishni yoqing.
- Loglarni `docker compose logs -f bot` orqali kuzating.
- HTTPS webhook kerak bo‘lsa `WEBHOOK_URL` ni sozlang; aks holda polling ishlaydi.

## Tuzilma
`app/handlers` Telegram oqimini, `app/services` biznes qoidalarini, `app/repositories` DB operatsiyalarini, `app/models` ORM modellarini, `app/keyboards` interfeysni, `app/states` FSM holatlarini boshqaradi.

## Huquqiy foydalanish
Bot faqat siz tarqatish huquqiga ega bo‘lgan anime materiallarini boshqarish uchun ishlatilishi kerak. Mualliflik huquqi bilan himoyalangan kontentni ruxsatsiz tarqatmang.
