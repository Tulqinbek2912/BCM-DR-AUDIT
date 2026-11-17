# BCM & DR AUDIT PRO
**Biznes uzluksizligi va avariyadan tiklanish xavfsizligi platformasi**
Mavzu: «Tashkilotlarning biznes uzluksizligi va avariyadan tiklash rejalari axborot xavfsizligi auditi».

Django 5 + Bootstrap 5 + Chart.js. Interfeys faqat o‘zbek tilida. Bootstrap, Bootstrap Icons va Chart.js loyiha ichiga (`static/vendor`) joylangan — internet ulanishisiz ham ishlaydi.

## 1. Tez ishga tushirish (lokal, SQLite)
```bash
python3 -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo          # DEMO TECHNOLOGY GROUP ma‘lumotlari
python manage.py test               # avtomatik testlar (24 ta)
python manage.py runserver
```
Brauzerda: http://127.0.0.1:8000/

## 2. Demo hisoblar
| Rol | Login | Parol |
|---|---|---|
| Administrator | `admin` | `Admin#2026Demo` (**birinchi kirishda parolni almashtirish majburiy**) |
| Axborot xavfsizligi auditori | `auditor_demo` | `Demo#2026Pass` |
| Tashkilot menejeri | `menejer_demo` | `Demo#2026Pass` |
| Kuzatuvchi | `kuzatuvchi_demo` | `Demo#2026Pass` |

Parollarni `DEMO_ADMIN_PASSWORD` / `DEMO_USER_PASSWORD` muhit o‘zgaruvchilari bilan o‘zgartirish mumkin. **Real foydalanishdan oldin demo hisoblarni o‘chiring yoki parollarini almashtiring**, DEMO yozuvlarni o‘chirish: «Tashkilotlar» bo‘limida DEMO TECHNOLOGY GROUP ni o‘chiring (bog‘liq barcha DEMO yozuvlar ham o‘chadi).

## 3. Rollar va ruxsatlar
| Bo‘lim | Administrator | Auditor | Menejer | Kuzatuvchi |
|---|---|---|---|---|
| Tashkilotlar, Risklar, Auditlar, Audit savollari | to‘liq | to‘liq | o‘qish | o‘qish |
| Aktivlar, BIA, BCP, DRP, Zaxira, Hodisalar | to‘liq | to‘liq | to‘liq | o‘qish |
| Faoliyat jurnali | ko‘rish | ko‘rish | — | — |
| Foydalanuvchilar | to‘liq | — | — | — |
Hisobotlarni (PDF/Excel) barcha rollar yuklab oladi.

## 4. Modullar
Boshqaruv paneli (bazadan hisoblangan 8 ko‘rsatkich + 5 ta Chart.js grafik) · Tashkilotlar · Axborot aktivlari · Risk baholash (E×T, 5×5 vizual matritsa, qoldiq xavf) · BIA (MTD/RTO/RPO) · BCP · DRP (interaktiv checklist) · Zaxira monitoringi · Auditlar va checklist (muvofiqlik % avtomatik, dalil fayllari) · Hodisalar · Faoliyat jurnali · PDF/Excel hisobotlar · Standartlar sahifasi.

**Risk darajalari:** 1–4 Past · 5–9 O‘rta · 10–16 Yuqori · 17–25 Kritik.
**Muvofiqlik:** Mos = 100%, Qisman mos = 50%, Mos emas = 0%; «Tegishli emas» va baholanmaganlar hisobga olinmaydi.
**Zaxira tekshiruvi:** tizim zaxira fayllarini o‘zi tekshirmaydi. «Yaxlitlik» va «Tiklash sinovi» faqat mas‘ul shaxs tekshiruv bajarilganini tasdiqlagandan so‘ng (ism va vaqt bilan) «Ha» bo‘ladi. DEMO yozuvlarda bu tasdiqlar ataylab bo‘sh.
**Standartlar:** ISO 22301, ISO/IEC 27001/27002/27031, NIST CSF, NIST SP 800-34 — faqat baholash uchun tayanch sifatida; bu **rasmiy sertifikatlash emas**.

## 5. Docker bilan ishga tushirish (PostgreSQL)
```bash
cp .env.example .env     # SECRET_KEY, ALLOWED_HOSTS, DB_PASSWORD ni o‘zgartiring
# lokal HTTP sinov uchun .env da:  SECURE_SSL=False
docker compose up --build -d
docker compose logs -f web
```
Ilova: http://localhost:8000/ . Konteyner ishga tushganda `migrate`, `collectstatic` va (`SEED_DEMO=1` bo‘lsa) `seed_demo` avtomatik bajariladi.

## 6. Internetga joylash (qadam-baqadam, arzon/bepul tarif)
Quyida Render.com misoli (Railway, Fly.io, VPS ham o‘xshash):
1. Loyihani GitHub’ga yuklang (`.env` va `db.sqlite3` `.gitignore` da).
2. Render.com → **New → Blueprint** → repozitoriyni tanlang. `render.yaml` Web Service va PostgreSQL’ni yaratadi.
3. Muhit o‘zgaruvchilarini tekshiring: `SECRET_KEY` (avtomatik), `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` (sizning domeningiz), `DATABASE_URL`.
4. Deploy tugagach HTTPS manzilini oching va `admin` bilan kiring, parolni almashtiring.
5. Haqiqiy foydalanish uchun `SEED_DEMO=0` qiling va demo hisoblarni o‘chiring.
6. **Eslatma:** bepul tarifda yuklangan dalil fayllari (`media/`) konteyner qayta ishga tushganda yo‘qolishi mumkin — doimiy disk (persistent disk) ulang yoki tarifni oshiring.
VPS’da: Docker + Nginx/Caddy (HTTPS, Let’s Encrypt) → `proxy_pass http://127.0.0.1:8000` va `X-Forwarded-Proto https` sarlavhasini uzating.

> Ushbu loyiha hali internetga joylanmagan. Joylash faqat yuqoridagi qadamlar bajarilib, sinovdan o‘tkazilgandan keyin «ishlayapti» deb hisoblansin.

## 7. Zaxira nusxa va tiklash
SQLite: `cp db.sqlite3 backup_$(date +%F).sqlite3` (tiklash — faylni joyiga qaytarish).
PostgreSQL (Docker):
```bash
docker compose exec db pg_dump -U bcm bcm_audit > backup_$(date +%F).sql
docker compose exec -T db psql -U bcm bcm_audit < backup_2026-01-01.sql      # tiklash
docker run --rm -v bcm_media:/m -v $PWD:/b alpine tar czf /b/media_backup.tgz -C /m .   # dalil fayllari
```
Zaxirani muntazam tiklab ko‘ring va natijani «Zaxira nusxalar» bo‘limida qayd eting.

## 8. Loyiha tuzilishi
```
manage.py · requirements.txt · Dockerfile · docker-compose.yml · render.yaml · gunicorn.conf.py · entrypoint.sh · .env.example
config/     settings (env orqali), urls, wsgi
accounts/   User (4 rol), ActivityLog, login/logout/parol, middleware (majburiy parol almashtirish)
audit/      models, registry (CRUD konfiguratsiyasi), views, reports (PDF/Excel), context, tests,
            management/commands/seed_demo.py
templates/  base, login, dashboard, list/form/confirm_delete (umumiy CRUD), matrix, drp_detail, backup_detail, audit_*, reports, standards
static/     css/app.css, js/app.js, js/dashboard.js, vendor/ (Bootstrap, Icons, Chart.js)
```

## 9. Cheklovlar
- Zaxira fayllari avtomatik tekshirilmaydi (faqat qo‘lda tasdiqlash qaydi).
- Kirish urinishlarini bloklash (brute-force lockout) yo‘q — jurnalga yoziladi; production’da reverse-proxy darajasida cheklang (masalan, Nginx `limit_req`) yoki `django-axes` qo‘shing.
- Ikki faktorli autentifikatsiya yo‘q.
- PDF’da faqat lotin yozuvi (Helvetica) ishlatilgan; Uzbek lotin harflari (o‘, g‘ — `‘` belgisi bilan) to‘g‘ri chiqadi, kirill yozuvi qo‘llab-quvvatlanmaydi.
- Hisobot bitta tashkilotning barcha ma‘lumotlarini oladi (xavflar, BCP, DRP, zaxira) — auditga bog‘lab alohida «snapshot» saqlanmaydi.
- Tashkilot bo‘yicha ma‘lumotlarni ajratish (multi-tenant ruxsatlari) yo‘q: barcha foydalanuvchilar barcha tashkilotlarni ko‘radi.
