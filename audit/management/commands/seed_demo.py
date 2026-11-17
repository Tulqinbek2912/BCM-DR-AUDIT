import os
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from accounts.models import User
from audit import models as m

ADMIN_PW = os.environ.get("DEMO_ADMIN_PASSWORD", "Admin#2026Demo")
USER_PW = os.environ.get("DEMO_USER_PASSWORD", "Demo#2026Pass")


class Command(BaseCommand):
    help = "DEMO TECHNOLOGY GROUP uchun namunaviy ma‘lumotlarni yaratadi (qayta ishga tushirish xavfsiz)."

    def add_arguments(self, p):
        p.add_argument("--reset", action="store_true", help="Avval mavjud DEMO yozuvlarni o‘chiradi")

    @transaction.atomic
    def handle(self, *a, **o):
        self.users()
        if o["reset"]:
            m.Organization.objects.filter(is_demo=True).delete()
        if m.Organization.objects.filter(is_demo=True).exists():
            self.stdout.write("DEMO ma‘lumotlar allaqachon mavjud (yangilash uchun --reset).")
            return
        self.data()
        self.stdout.write(self.style.SUCCESS("DEMO ma‘lumotlar yaratildi."))

    def users(self):
        specs = [("admin", "Administrator", "admin", ADMIN_PW, True), ("auditor_demo", "Auditor Demo", "auditor", USER_PW, False),
                 ("menejer_demo", "Menejer Demo", "manager", USER_PW, False), ("kuzatuvchi_demo", "Kuzatuvchi Demo", "viewer", USER_PW, False)]
        for un, name, role, pw, must in specs:
            u, created = User.objects.get_or_create(username=un, defaults=dict(first_name=name.split()[0], last_name=" ".join(name.split()[1:]),
                                                                              role=role, is_staff=role == "admin", is_superuser=role == "admin",
                                                                              email=f"{un}@demo.local", must_change_password=must))
            if created:
                u.set_password(pw)
                u.save()

    def data(self):
        now = timezone.now()
        D = dict(is_demo=True)
        org = m.Organization.objects.create(name="DEMO TECHNOLOGY GROUP", industry="Axborot texnologiyalari va moliyaviy xizmatlar",
            address="Toshkent sh., Amir Temur ko‘chasi, 100 (xayoliy manzil)", contact_person="Karimov Aziz", email="info@demo-tech.example",
            employees=240, servers=35, description="Namunaviy (xayoliy) tashkilot — faqat namoyish uchun.", **D)
        # Aktivlar
        A = [("ERP serveri", "Server", "10.10.1.10", "Kritik", "IT bo‘limi boshlig‘i", "Himoyalangan"),
             ("Asosiy ma‘lumotlar bazasi (PostgreSQL)", "Ma‘lumotlar bazasi", "10.10.1.20", "Kritik", "DBA", "Himoyalangan"),
             ("Mijozlar CRM tizimi", "Ilova / tizim", "10.10.1.30", "Yuqori", "Savdo direktori", "Qisman himoyalangan"),
             ("Korporativ elektron pochta", "Ilova / tizim", "10.10.1.40", "Yuqori", "IT bo‘limi boshlig‘i", "Himoyalangan"),
             ("Asosiy marshrutizator", "Tarmoq qurilmasi", "10.10.0.1", "Kritik", "Tarmoq muhandisi", "Himoyalangan"),
             ("Xavfsizlik devori (Firewall)", "Tarmoq qurilmasi", "10.10.0.2", "Kritik", "Axborot xavfsizligi rahbari", "Himoyalangan"),
             ("Fayl serveri", "Server", "10.10.1.50", "O‘rta", "IT bo‘limi boshlig‘i", "Qisman himoyalangan"),
             ("Zaxira saqlash tizimi (NAS)", "Server", "10.10.2.10", "Yuqori", "Tizim administratori", "Qisman himoyalangan"),
             ("Xodimlar ish stansiyalari", "Ish stansiyasi", None, "O‘rta", "IT yordam xizmati", "Qisman himoyalangan"),
             ("Moliyaviy hisobotlar ma‘lumotlari", "Ma‘lumot", None, "Yuqori", "Bosh buxgalter", "Qisman himoyalangan")]
        assets = [m.Asset.objects.create(organization=org, name=n, asset_type=t, ip_address=ip, criticality=c, owner=ow, protection_status=p,
                                         description=f"{n} — namunaviy aktiv.", **D) for n, t, ip, c, ow, p in A]
        # Risklar: tahdid, zaiflik, aktiv idx, E, T, mavjud nazorat, tavsiya, qE, qT, holat
        R = [("Ransomware hujumi", "Zaxira nusxalar tarmoqdan ajratilmagan", 7, 4, 5, "Antivirus", "Zaxirani offline/immutable saqlash, tarmoqni segmentlash", 2, 4, "Jarayonda"),
             ("Ma‘lumotlar bazasi serveri nosozligi", "Replikatsiya yo‘q", 1, 3, 5, "Kunlik zaxira", "Hot-standby replika o‘rnatish", 2, 3, "Jarayonda"),
             ("Fishing orqali hisob buzilishi", "Ko‘p faktorli autentifikatsiya yo‘q", 3, 4, 4, "Spam filtr", "MFA joriy etish, xodimlarni o‘qitish", 2, 3, "Ochiq"),
             ("Elektr ta‘minoti uzilishi", "UPS va generator quvvati yetarli emas", 0, 3, 4, "UPS (30 daqiqa)", "Generator va UPS quvvatini oshirish", 2, 3, "Ochiq"),
             ("Ruxsatsiz tarmoqqa kirish", "Tarmoq segmentatsiyasi yetarli emas", 4, 3, 4, "Firewall qoidalari", "VLAN segmentatsiyasi va IDS/IPS", 2, 3, "Jarayonda"),
             ("Ma‘lumot sızishi (insayder)", "Imtiyozlarni muntazam ko‘rib chiqish yo‘q", 9, 3, 5, "Rol asosidagi kirish", "Kirish huquqlarini choraklik qayta ko‘rish, DLP", 2, 4, "Ochiq"),
             ("DDoS hujumi", "Provayder darajasida himoya yo‘q", 5, 3, 3, "Rate limiting", "DDoS himoya xizmatini ulash", 2, 2, "Ochiq"),
             ("Zaxira nusxadan tiklash muvaffaqiyatsizligi", "Tiklash sinovlari o‘tkazilmagan", 7, 4, 4, "Zaxira monitoringi", "Choraklik tiklash sinovlari", 2, 3, "Jarayonda"),
             ("Server xonasida yong‘in", "Gaz o‘chirish tizimi yo‘q", 0, 2, 5, "Yong‘in signalizatsiyasi", "Gazli yong‘in o‘chirish o‘rnatish", 1, 5, "Qabul qilingan"),
             ("Dasturiy ta‘minot zaifliklari (patch yo‘qligi)", "Yamoqlarni o‘rnatish jarayoni tartibsiz", 6, 4, 3, "Oylik yangilash", "Avtomatik patch management", 2, 2, "Jarayonda"),
             ("Jurnallar yo‘qolishi", "Markazlashgan log tizimi yo‘q", 1, 3, 3, "Mahalliy loglar", "SIEM/markaziy log serveri joriy etish", 1, 3, "Ochiq"),
             ("Tabiiy ofat (zilzila) tufayli ma‘lumot markazi yo‘qolishi", "Zaxira sayt yo‘q", 0, 1, 5, "Hududiy zaxira nusxa", "Muqobil (DR) sayt tashkil etish", 1, 4, "Ochiq"),
             ("Ish stansiyalarida zararli dastur", "USB qurilmalar nazorat qilinmaydi", 8, 3, 2, "Antivirus", "Endpoint himoyasi (EDR), USB cheklovi", 1, 2, "Kamaytirilgan"),
             ("Kalit xodim ketishi (bilimlar yo‘qolishi)", "Hujjatlashtirish yetarli emas", 1, 2, 3, "Ichki wiki", "Runbook va almashtirish rejasi", 1, 2, "Ochiq"),
             ("Shifrlanmagan ma‘lumot uzatilishi", "TLS sozlamalari eskirgan", 2, 2, 3, "VPN", "TLS 1.2+ ni majburiy qilish", 1, 2, "Yopilgan")]
        for t, v, ai, L, I, c, mit, rl, ri, st in R:
            m.Risk.objects.create(organization=org, threat=t, vulnerability=v, asset=assets[ai], owner=assets[ai].owner, likelihood=L, impact=I,
                                  existing_controls=c, mitigation=mit, residual_likelihood=rl, residual_impact=ri, status=st, **D)
        # BIA
        B = [("Onlayn to‘lovlarni qayta ishlash", "Kritik", "Kritik", "Yuqori", 4, 2, 0.5, "Kritik"), ("Mijozlarga xizmat ko‘rsatish (CRM)", "Yuqori", "Yuqori", "O‘rta", 12, 6, 4, "Yuqori"),
             ("Buxgalteriya va hisobotlar", "Yuqori", "O‘rta", "Yuqori", 24, 12, 8, "Yuqori"), ("Elektron pochta va kommunikatsiya", "O‘rta", "Yuqori", "Past", 24, 8, 24, "O‘rta"),
             ("Ish haqi hisoblash", "O‘rta", "O‘rta", "Yuqori", 72, 24, 24, "O‘rta"), ("Ichki fayl almashinuvi", "Past", "O‘rta", "Past", 72, 48, 24, "Past"),
             ("Axborot xavfsizligi monitoringi", "Yuqori", "Yuqori", "Yuqori", 8, 4, 1, "Yuqori"), ("Veb-sayt va marketing", "O‘rta", "Past", "Past", 48, 24, 24, "Past"),
             ("Kadrlar boshqaruvi", "Past", "O‘rta", "O‘rta", 72, 48, 24, "Past"), ("Ta‘minot va logistika", "O‘rta", "Yuqori", "O‘rta", 24, 12, 12, "O‘rta")]
        for p, f, op, lg, mtd, rto, rpo, cr in B:
            m.BIA.objects.create(organization=org, process=p, financial_impact=f, operational_impact=op, legal_impact=lg, mtd_hours=mtd, rto_hours=rto, rpo_hours=rpo, criticality=cr, **D)
        # BCP
        P = [("Axborot tizimlari uzilishida uzluksizlik rejasi", "IT bo‘limi boshlig‘i", "Tizim uzilsa: 1) hodisa boshqaruv guruhi chaqiriladi; 2) ta‘sir baholanadi; 3) DRP ishga tushiriladi.", "Qo‘lda (qog‘oz) buyurtma qabul qilish, rezerv ofis.", "SMS/Telegram guruhi orqali xodimlar, mijozlar va regulyatorga xabar berish.", 120, "Tasdiqlangan"),
             ("Ofisga kirish imkoni bo‘lmaganda masofaviy ish rejasi", "HR direktori", "Xodimlar VPN orqali uyda ishlashga o‘tadi; kritik jarayonlar ro‘yxati e‘lon qilinadi.", "Uydan ishlash, muqobil koworking.", "Rahbariyat har 4 soatda holat haqida yangilanish beradi.", 200, "Tasdiqlangan"),
             ("Asosiy yetkazib beruvchi ishdan chiqqanda reja", "Ta‘minot rahbari", "Zaxira yetkazib beruvchilarga o‘tish tartibi.", "Muqobil yetkazib beruvchi shartnomalari.", "Yetkazib beruvchilar bilan aloqa jadvali.", 30, "Ko‘rib chiqilmoqda"),
             ("Kiberhodisa vaqtida kommunikatsiya rejasi", "Axborot xavfsizligi rahbari", "Hodisani aniqlash, izolyatsiya qilish, dalillarni saqlash.", "Muhim xizmatlarni izolyatsiya qilingan muhitda ishlatish.", "Mijozlar va nazorat organlariga xabar berish shablonlari.", -10, "Muddati o‘tgan"),
             ("Ma‘lumot markazi yo‘qolganda reja", "Bosh direktor o‘rinbosari", "Muqobil saytga o‘tish bo‘yicha qaror qabul qilish tartibi.", "Bulutli muqobil muhit.", "Favqulodda aloqa daraxti.", 300, "Qoralama")]
        for t, r, e, alt, comm, days, st in P:
            m.BCPPlan.objects.create(organization=org, title=t, responsible=r, emergency_procedures=e, alternative_operations=alt, communication_plan=comm,
                                     review_date=(now + timedelta(days=days)).date(), approval_status=st, **D)
        # DRP
        S = [("Server nosozligi", "ERP serveri apparat nosozligi tufayli ishdan chiqdi.", "Kritik", "Nosozlikni tasdiqlash\nZaxira serverni ishga tushirish\nZaxira nusxadan tiklash\nTizim funksionalligini tekshirish\nFoydalanuvchilarga xabar berish", "Tizim administratori", 4, 3.5, "Tiklandi", 5),
             ("Ma‘lumotlar bazasi nosozligi", "Asosiy ma‘lumotlar bazasi buzildi.", "Kritik", "Yozuvlarni to‘xtatish\nOxirgi yaxlit zaxirani aniqlash\nBazani tiklash\nMa‘lumotlar yaxlitligini tekshirish\nYozuvni qayta yoqish", "DBA", 6, None, "Jarayonda", 2),
             ("Ransomware (to‘lov dasturi)", "Fayl serverlari shifrlandi.", "Kritik", "Zararlangan tizimlarni tarmoqdan uzish\nHodisa guruhini yig‘ish\nDalillarni saqlash\nToza zaxiradan tiklash\nParollarni almashtirish\nXavfsizlik devorini kuchaytirish", "Axborot xavfsizligi rahbari", 24, None, "Rejalashtirilgan", 0),
             ("Tarmoq nosozligi", "Asosiy marshrutizator ishdan chiqdi.", "Yuqori", "Rezerv kanalga o‘tish\nMarshrutizatorni almashtirish\nKonfiguratsiyani tiklash\nAloqani tekshirish", "Tarmoq muhandisi", 3, 2.5, "Tiklandi", 4),
             ("Elektr ta‘minoti uzilishi", "Bino bo‘yicha elektr uzildi, UPS zaryadi tugamoqda.", "Yuqori", "UPSga o‘tishni tasdiqlash\nKritik bo‘lmagan tizimlarni o‘chirish\nGeneratorni ishga tushirish\nTizimlarni ketma-ket qayta yoqish", "Obyekt menejeri", 2, None, "Rejalashtirilgan", 1)]
        for t, d, pr, steps, resp, est, act, st, done in S:
            sc = m.DRPScenario.objects.create(organization=org, scenario_type=t, description=d, priority=pr, recovery_steps=steps, responsible=resp, estimated_hours=est, actual_hours=act, status=st, **D)
            sc.sync_steps()
            for s in list(sc.steps.all())[:done]:
                s.done = True
                s.save()
        # Zaxira (tekshiruv/ sinov qaydlari ataylab bo‘sh qoldirilgan — real tekshiruv bajarilmagan)
        K = [("ERP kunlik to‘liq zaxira", "To‘liq", "NAS (10.10.2.10) + bulut", "Har kuni 02:00", 1, 420.5, True, "Muvaffaqiyatli"),
             ("Ma‘lumotlar bazasi WAL arxivi", "Inkremental", "NAS (10.10.2.10)", "Har soatda", 0, 85.2, True, "Muvaffaqiyatli"),
             ("Fayl serveri haftalik zaxira", "To‘liq", "Lenta kutubxonasi", "Har yakshanba", 5, 1200, False, "Tekshirish kerak"),
             ("Elektron pochta zaxirasi", "Differensial", "Bulut (S3-mos)", "Har kuni 03:00", 2, 310, True, "Xatolik"),
             ("Virtual mashinalar snapshoti", "Snapshot", "SAN", "Har 6 soatda", 0, 640, False, "Kutilmoqda")]
        for n, t, loc, fr, ago, sz, enc, st in K:
            m.Backup.objects.create(organization=org, name=n, backup_type=t, storage_location=loc, frequency=fr, last_backup=now - timedelta(days=ago, hours=1),
                                    next_backup=now + timedelta(hours=12), size_gb=sz, encrypted=enc, status=st, **D)
        # Audit va checklist
        au = m.Audit.objects.create(organization=org, title="2026 yil BCM & DR axborot xavfsizligi auditi", audit_date=now.date(), status="Jarayonda",
                                    auditor=User.objects.get(username="auditor_demo"),
                                    scope="Axborot tizimlari, ma‘lumotlar bazasi, zaxira nusxalash, BCP va DRP jarayonlari, hodisalarni boshqarish.", **D)
        Q = [("Kirishni boshqarish", "Kirish huquqlari eng kam imtiyoz tamoyili asosida beriladimi?", "ISO 27002 5.15", "Qisman mos", "Choraklik qayta ko‘rish yo‘q."),
             ("Kirishni boshqarish", "Ishdan ketgan xodimlarning hisoblari o‘z vaqtida o‘chiriladimi?", "ISO 27002 5.18", "Mos", ""),
             ("Autentifikatsiya", "Administrator hisoblari uchun ko‘p faktorli autentifikatsiya qo‘llanadimi?", "ISO 27002 8.5", "Mos emas", "MFA faqat pochta uchun."),
             ("Autentifikatsiya", "Parol siyosati (uzunlik, murakkablik) belgilanganmi?", "ISO 27002 5.17", "Mos", ""),
             ("Tarmoq xavfsizligi", "Tarmoq segmentlarga ajratilganmi va firewall qoidalari ko‘rib chiqiladimi?", "ISO 27002 8.22", "Qisman mos", ""),
             ("Server xavfsizligi", "Serverlar uchun xavfsizlik yamoqlari muntazam o‘rnatiladimi?", "NIST CSF PR.IP", "Qisman mos", "Oylik, istisnolar bor."),
             ("Ma‘lumotlar bazasi xavfsizligi", "Ma‘lumotlar bazasi shifrlanganmi va kirish jurnallashtiriladimi?", "ISO 27002 8.24", "Mos", ""),
             ("Ma‘lumotlar bazasi xavfsizligi", "Ma‘lumotlar bazasi replikatsiyasi mavjudmi?", "ISO 27031", "Mos emas", ""),
             ("Zaxira nusxa xavfsizligi", "Zaxira nusxalar shifrlanganmi?", "ISO 27002 8.13", "Qisman mos", "3 tadan 2 tasi shifrlangan."),
             ("Zaxira nusxa xavfsizligi", "Zaxira nusxalardan tiklash muntazam sinovdan o‘tkaziladimi?", "NIST SP 800-34", "Mos emas", "Sinov o‘tkazilmagan."),
             ("Hodisalarni boshqarish", "Axborot xavfsizligi hodisalari uchun rasmiy tartib mavjudmi?", "ISO 27002 5.24", "Mos", ""),
             ("Hodisalarni boshqarish", "Hodisalar tahlil qilinib, saboqlar hujjatlashtiriladimi?", "ISO 27002 5.27", "Qisman mos", ""),
             ("Jurnallashtirish", "Muhim tizimlar jurnallari markaziy joyda saqlanadimi?", "ISO 27002 8.15", "Mos emas", ""),
             ("Jurnallashtirish", "Jurnallar kamida 12 oy saqlanadimi?", "ISO 27002 8.15", "Tegishli emas", "Muddat siyosatda belgilanmagan."),
             ("Jismoniy xavfsizlik", "Server xonasiga kirish nazorat qilinadimi?", "ISO 27002 7.2", "Mos", ""),
             ("Jismoniy xavfsizlik", "Yong‘in va elektr uzilishiga qarshi himoya mavjudmi?", "ISO 27002 7.5", "Qisman mos", "Gazli o‘chirish yo‘q."),
             ("Ma‘lumotlarni himoya qilish", "Shaxsiy ma‘lumotlar tasniflangan va himoyalanganmi?", "ISO 27002 5.12", "Qisman mos", ""),
             ("Ma‘lumotlarni himoya qilish", "Ma‘lumotlarni uzatishda shifrlash qo‘llanadimi?", "ISO 27002 8.24", "Mos", ""),
             ("BCP va DRP", "BIA o‘tkazilgan va RTO/RPO belgilanganmi?", "ISO 22301 8.2", "Mos", ""),
             ("BCP va DRP", "BCP/DRP rejalari yiliga kamida bir marta sinovdan o‘tkaziladimi?", "ISO 22301 8.5", "", "")]
        for c, q, ref, ans, com in Q:
            m.ChecklistItem.objects.create(audit=au, category=c, question=q, standard_ref=ref, answer=ans, comment=com, **D)
        # Hodisalar
        I = [("Fishing", "Yuqori", "Korporativ pochta", 9, "Bir nechta xodimga fishing xati kelgan, 1 ta hisob buzilgan.", "Hisob bloklandi, parol almashtirildi.", "Tekshirilmoqda"),
             ("Apparat nosozligi", "Kritik", "ERP serveri", 20, "ERP serveri diskida nosozlik.", "Zaxira serverga o‘tildi, disk almashtirildi.", "Yopilgan"),
             ("Xizmat ko‘rsatishdan voz kechish (DoS)", "O‘rta", "Veb-sayt", 15, "Veb-saytga g‘ayritabiiy trafik.", "Rate limit yoqildi.", "Bartaraf etildi"),
             ("Zararli dastur", "Yuqori", "Ish stansiyalari", 3, "2 ta kompyuterda troyan aniqlandi.", "Izolyatsiya qilindi, qayta o‘rnatildi.", "Ochiq"),
             ("Elektr uzilishi", "O‘rta", "Server xonasi", 30, "20 daqiqalik elektr uzilishi.", "UPS ishladi.", "Yopilgan")]
        for t, sv, sy, ago, d, resp, st in I:
            m.Incident.objects.create(organization=org, incident_type=t, severity=sv, affected_systems=sy, incident_date=now - timedelta(days=ago), description=d,
                                      response_actions=resp, responsible="Axborot xavfsizligi guruhi", status=st, **D)
