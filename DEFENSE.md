# Himoya (defense) uchun namoyish qo‘llanmasi — taxminan 10 daqiqa
**Tayyorgarlik:** `python manage.py migrate && python manage.py seed_demo && python manage.py runserver`; `admin` / `Admin#2026Demo` bilan kiring (parolni almashtiring).

1. **(1 daq) Maqsad va muammo.** Tashkilotlarda BCP/DRP mavjudligi ≠ ishlashi; audit platformasi uzluksizlikni xavf, BIA, zaxira va tiklash ko‘rsatkichlari bilan baholaydi.
2. **(2 daq) Boshqaruv paneli.** 8 ta ko‘rsatkich va 5 ta grafik bazadan hisoblanadi. Isbot: yangi xavf qo‘shing (Risk baholash → Yangi, E=5, T=5) → panelda «Kritik xavflar» +1 bo‘ladi.
3. **(1.5 daq) Risk matritsasi 5×5.** Ball = E×T, daraja chegaralari 1–4/5–9/10–16/17–25; dastlabki va qoldiq xavfni almashtiring.
4. **(1 daq) BIA.** MTD/RTO/RPO ma‘nosi; RTO>MTD kiritilsa tizim xato beradi.
5. **(1.5 daq) BCP va DRP.** DRP → «Ransomware» → checklist bosqichlarini belgilang, progress real vaqtda o‘zgaradi va panelda «DRP tayyorgarligi» yangilanadi.
6. **(1 daq) Zaxira monitoringi.** Yaxlitlik/tiklash sinovi faqat tasdiqlangandagina «Ha» — tizim soxta tekshiruvni da‘vo qilmaydi (akademik halollik nuqtasi).
7. **(1.5 daq) Audit.** Auditlar → ochish → «Baholashni to‘ldirish» → bir nechta bahoni o‘zgartiring → muvofiqlik % qayta hisoblanadi; dalil faylini biriktiring.
8. **(1 daq) Hisobotlar.** PDF va Excel yuklab oling; PDF tarkibi: tashkilot, qamrov, xulosa, risk/BCP/DRP/zaxira, checklist, tavsiyalar, auditor.
9. **(0.5 daq) Xavfsizlik.** 4 rol, majburiy parol almashtirish, faoliyat jurnali (kirish urinishlari, o‘zgarishlar, hisobotlar). Kuzatuvchi bilan kirib, yozish taqiqlanganini ko‘rsating (403).

**Ehtimoliy savollar:** *Standartlarga muvofiqmi?* — Yo‘q, tayanch sifatida (sertifikat emas). *Muvofiqlik foizi qanday?* — Mos 100/Qisman 50/Mos emas 0, T/E hisobga olinmaydi. *Cheklovlar?* — README §9.
