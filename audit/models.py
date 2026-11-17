from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models


def C(*items):
    return [(x, x) for x in items]


LEVELS = C("Past", "O‘rta", "Yuqori", "Kritik")
LEVEL_KEY = {"Past": "low", "O‘rta": "mid", "Yuqori": "high", "Kritik": "crit"}
SCALE = [MinValueValidator(1), MaxValueValidator(5)]
ANSWER_SCORE = {"Mos": 1.0, "Qisman mos": 0.5, "Mos emas": 0.0}


def risk_level(score):
    if score <= 4:
        return "Past"
    if score <= 9:
        return "O‘rta"
    if score <= 16:
        return "Yuqori"
    return "Kritik"


def compliance_of(items):
    """Muvofiqlik foizi: Mos=100%, Qisman mos=50%, Mos emas=0%. 'Tegishli emas' va baholanmaganlar hisobga olinmaydi."""
    vals = [ANSWER_SCORE[i.answer] for i in items if i.answer in ANSWER_SCORE]
    return round(sum(vals) / len(vals) * 100, 1) if vals else None


def validate_size(f):
    if f.size > 5 * 1024 * 1024:
        raise ValidationError("Fayl hajmi 5 MB dan oshmasligi kerak.")


class Base(models.Model):
    is_demo = models.BooleanField("DEMO yozuv", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Organization(Base):
    name = models.CharField("Tashkilot nomi", max_length=200)
    industry = models.CharField("Soha", max_length=120)
    address = models.CharField("Manzil", max_length=250, blank=True)
    contact_person = models.CharField("Mas‘ul shaxs", max_length=150)
    email = models.EmailField("Elektron pochta", blank=True)
    employees = models.PositiveIntegerField("Xodimlar soni", default=0)
    servers = models.PositiveIntegerField("Serverlar soni", default=0)
    description = models.TextField("Tavsif", blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Tashkilot"

    def __str__(self):
        return self.name


class Asset(Base):
    TYPES = C("Server", "Ma‘lumotlar bazasi", "Tarmoq qurilmasi", "Ilova / tizim", "Ish stansiyasi", "Ma‘lumot", "Boshqa")
    PROT = C("Himoyalangan", "Qisman himoyalangan", "Himoyalanmagan")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, verbose_name="Tashkilot")
    name = models.CharField("Aktiv nomi", max_length=200)
    asset_type = models.CharField("Aktiv turi", max_length=40, choices=TYPES)
    ip_address = models.GenericIPAddressField("IP manzil", null=True, blank=True)
    criticality = models.CharField("Muhimlik darajasi", max_length=10, choices=LEVELS, default="O‘rta")
    owner = models.CharField("Egasi", max_length=150)
    description = models.TextField("Tavsif", blank=True)
    protection_status = models.CharField("Himoya holati", max_length=30, choices=PROT, default="Qisman himoyalangan")

    class Meta:
        verbose_name = "Axborot aktivi"

    def __str__(self):
        return self.name


class Risk(Base):
    STATUS = C("Ochiq", "Jarayonda", "Kamaytirilgan", "Qabul qilingan", "Yopilgan")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, verbose_name="Tashkilot")
    threat = models.CharField("Tahdid", max_length=250)
    vulnerability = models.CharField("Zaiflik", max_length=250)
    asset = models.ForeignKey(Asset, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Ta‘sirlanadigan aktiv")
    owner = models.CharField("Xavf egasi", max_length=150)
    likelihood = models.PositiveSmallIntegerField("Ehtimollik (1–5)", validators=SCALE, default=3)
    impact = models.PositiveSmallIntegerField("Ta‘sir (1–5)", validators=SCALE, default=3)
    existing_controls = models.TextField("Mavjud nazorat choralari", blank=True)
    mitigation = models.TextField("Kamaytirish bo‘yicha tavsiya", blank=True)
    residual_likelihood = models.PositiveSmallIntegerField("Qoldiq ehtimollik (1–5)", validators=SCALE, default=1)
    residual_impact = models.PositiveSmallIntegerField("Qoldiq ta‘sir (1–5)", validators=SCALE, default=1)
    status = models.CharField("Holati", max_length=20, choices=STATUS, default="Ochiq")

    class Meta:
        verbose_name = "Xavf"

    @property
    def score(self):
        return self.likelihood * self.impact

    @property
    def level(self):
        return risk_level(self.score)

    @property
    def residual_score(self):
        return self.residual_likelihood * self.residual_impact

    @property
    def residual_level(self):
        return risk_level(self.residual_score)

    def __str__(self):
        return self.threat


class BIA(Base):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, verbose_name="Tashkilot")
    process = models.CharField("Biznes jarayon", max_length=200)
    financial_impact = models.CharField("Moliyaviy ta‘sir", max_length=10, choices=LEVELS)
    operational_impact = models.CharField("Operatsion ta‘sir", max_length=10, choices=LEVELS)
    legal_impact = models.CharField("Huquqiy ta‘sir", max_length=10, choices=LEVELS)
    mtd_hours = models.DecimalField("MTD — maksimal ruxsat etilgan to‘xtash (soat)", max_digits=7, decimal_places=1,
                                    help_text="Jarayon to‘xtab turishi mumkin bo‘lgan eng uzun muddat; undan keyin zarar tiklab bo‘lmas darajada bo‘ladi.")
    rto_hours = models.DecimalField("RTO — tiklash vaqti maqsadi (soat)", max_digits=7, decimal_places=1,
                                    help_text="Uzilishdan keyin tizim/jarayon qancha vaqt ichida qayta ishga tushirilishi kerak. RTO MTD dan oshmasligi lozim.")
    rpo_hours = models.DecimalField("RPO — tiklash nuqtasi maqsadi (soat)", max_digits=7, decimal_places=1,
                                    help_text="Ma‘lumotlarning eng ko‘pi bilan qancha vaqtlik yo‘qotilishiga yo‘l qo‘yiladi (oxirgi zaxira nusxadan keyingi muddat).")
    criticality = models.CharField("Muhimlik darajasi", max_length=10, choices=LEVELS, default="O‘rta")

    class Meta:
        verbose_name = "BIA yozuvi"

    def clean(self):
        if self.rto_hours is not None and self.mtd_hours is not None and self.rto_hours > self.mtd_hours:
            raise ValidationError({"rto_hours": "RTO qiymati MTD dan katta bo‘lishi mumkin emas."})

    def __str__(self):
        return self.process


class BCPPlan(Base):
    STATUS = C("Qoralama", "Ko‘rib chiqilmoqda", "Tasdiqlangan", "Muddati o‘tgan")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, verbose_name="Tashkilot")
    title = models.CharField("Uzluksizlik rejasi nomi", max_length=200)
    responsible = models.CharField("Mas‘ul shaxs", max_length=150)
    emergency_procedures = models.TextField("Favqulodda tartib-qoidalar")
    alternative_operations = models.TextField("Muqobil faoliyat tartibi", blank=True)
    communication_plan = models.TextField("Aloqa rejasi", blank=True)
    review_date = models.DateField("Qayta ko‘rib chiqish sanasi")
    approval_status = models.CharField("Tasdiqlash holati", max_length=20, choices=STATUS, default="Qoralama")

    class Meta:
        verbose_name = "BCP"

    def __str__(self):
        return self.title


class DRPScenario(Base):
    TYPES = C("Server nosozligi", "Ma‘lumotlar bazasi nosozligi", "Kiberhujum", "Ransomware (to‘lov dasturi)",
              "Tarmoq nosozligi", "Elektr ta‘minoti uzilishi", "Tabiiy ofat")
    STATUS = C("Rejalashtirilgan", "Jarayonda", "Tiklandi", "Muvaffaqiyatsiz")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, verbose_name="Tashkilot")
    scenario_type = models.CharField("Stsenariy", max_length=60, choices=TYPES)
    description = models.TextField("Hodisa tavsifi")
    priority = models.CharField("Ustuvorlik", max_length=10, choices=LEVELS, default="Yuqori")
    recovery_steps = models.TextField("Tiklash bosqichlari", help_text="Har bir bosqichni alohida qatorga yozing — ular interaktiv nazorat ro‘yxatiga aylanadi.")
    responsible = models.CharField("Mas‘ul shaxs", max_length=150)
    estimated_hours = models.DecimalField("Taxminiy tiklash vaqti (soat)", max_digits=7, decimal_places=1)
    actual_hours = models.DecimalField("Haqiqiy tiklash vaqti (soat)", max_digits=7, decimal_places=1, null=True, blank=True)
    status = models.CharField("Tiklash holati", max_length=20, choices=STATUS, default="Rejalashtirilgan")

    class Meta:
        verbose_name = "DRP stsenariysi"

    def __str__(self):
        return f"{self.scenario_type}"

    def sync_steps(self):
        lines = [x.strip() for x in self.recovery_steps.splitlines() if x.strip()]
        existing = {s.text: s for s in self.steps.all()}
        for i, t in enumerate(lines, 1):
            s = existing.pop(t, None)
            if s:
                if s.order != i:
                    s.order = i
                    s.save(update_fields=["order"])
            else:
                DRPStep.objects.create(scenario=self, text=t, order=i)
        for s in existing.values():
            s.delete()

    @property
    def progress_pct(self):
        total = self.steps.count()
        return round(self.steps.filter(done=True).count() / total * 100) if total else 0

    @property
    def progress(self):
        return f"{self.progress_pct}%"


class DRPStep(models.Model):
    scenario = models.ForeignKey(DRPScenario, on_delete=models.CASCADE, related_name="steps")
    order = models.PositiveSmallIntegerField(default=0)
    text = models.CharField(max_length=400)
    done = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "id"]


class Backup(Base):
    TYPES = C("To‘liq", "Inkremental", "Differensial", "Snapshot")
    STATUS = C("Muvaffaqiyatli", "Xatolik", "Kutilmoqda", "Tekshirish kerak")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, verbose_name="Tashkilot")
    name = models.CharField("Zaxira nusxa nomi", max_length=200)
    backup_type = models.CharField("Turi", max_length=20, choices=TYPES)
    storage_location = models.CharField("Saqlash joyi", max_length=250)
    frequency = models.CharField("Takrorlanish chastotasi", max_length=80)
    last_backup = models.DateTimeField("Oxirgi zaxira", null=True, blank=True)
    next_backup = models.DateTimeField("Keyingi zaxira", null=True, blank=True)
    size_gb = models.DecimalField("Hajmi (GB)", max_digits=10, decimal_places=2, default=0)
    encrypted = models.BooleanField("Shifrlangan", default=False)
    status = models.CharField("Holati", max_length=20, choices=STATUS, default="Kutilmoqda")
    # Quyidagi maydonlar faqat foydalanuvchi tekshiruvni haqiqatan bajarganini tasdiqlaganda to‘ldiriladi
    integrity_verified_at = models.DateTimeField("Yaxlitlik tekshirilgan vaqt", null=True, blank=True)
    integrity_verified_by = models.CharField("Yaxlitlikni tasdiqlagan", max_length=150, blank=True)
    restore_tested_at = models.DateTimeField("Tiklash sinovi vaqti", null=True, blank=True)
    restore_tested_by = models.CharField("Sinovni tasdiqlagan", max_length=150, blank=True)

    class Meta:
        verbose_name = "Zaxira nusxa"

    @property
    def integrity_checked(self):
        return self.integrity_verified_at is not None

    @property
    def restore_tested(self):
        return self.restore_tested_at is not None

    def __str__(self):
        return self.name


class Audit(Base):
    STATUS = C("Rejalashtirilgan", "Jarayonda", "Yakunlangan")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, verbose_name="Tashkilot")
    title = models.CharField("Audit nomi", max_length=200)
    scope = models.TextField("Audit qamrovi")
    audit_date = models.DateField("Audit sanasi")
    status = models.CharField("Holati", max_length=20, choices=STATUS, default="Jarayonda")
    auditor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Auditor")
    summary = models.TextField("Qisqacha xulosa (ixtiyoriy)", blank=True)
    conclusion = models.TextField("Yakuniy xulosa (ixtiyoriy)", blank=True)

    class Meta:
        ordering = ["-audit_date", "-id"]
        verbose_name = "Audit"

    @property
    def compliance(self):
        return compliance_of(self.items.all())

    @property
    def compliance_text(self):
        c = self.compliance
        return "—" if c is None else f"{c}%"

    def __str__(self):
        return self.title


class ChecklistItem(Base):
    CATEGORIES = C("Kirishni boshqarish", "Autentifikatsiya", "Tarmoq xavfsizligi", "Server xavfsizligi",
                   "Ma‘lumotlar bazasi xavfsizligi", "Zaxira nusxa xavfsizligi", "Hodisalarni boshqarish",
                   "Jurnallashtirish", "Jismoniy xavfsizlik", "Ma‘lumotlarni himoya qilish", "BCP va DRP")
    ANSWERS = C("Mos", "Qisman mos", "Mos emas", "Tegishli emas")
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name="items", verbose_name="Audit")
    category = models.CharField("Bo‘lim", max_length=60, choices=CATEGORIES)
    question = models.CharField("Savol / talab", max_length=500)
    standard_ref = models.CharField("Standart havolasi", max_length=120, blank=True)
    answer = models.CharField("Baho", max_length=20, choices=ANSWERS, blank=True)
    comment = models.TextField("Auditor izohi", blank=True)
    evidence = models.FileField("Dalil (fayl)", upload_to="evidence/%Y/%m/", blank=True,
                                validators=[FileExtensionValidator(["pdf", "png", "jpg", "jpeg", "docx", "xlsx", "txt"]), validate_size])

    class Meta:
        ordering = ["id"]
        verbose_name = "Audit savoli"

    @property
    def has_evidence(self):
        return bool(self.evidence)

    def __str__(self):
        return self.question


class Incident(Base):
    TYPES = C("Zararli dastur", "Fishing", "Ruxsatsiz kirish", "Xizmat ko‘rsatishdan voz kechish (DoS)",
              "Ma‘lumot sızishi", "Apparat nosozligi", "Elektr uzilishi", "Boshqa")
    STATUS = C("Ochiq", "Tekshirilmoqda", "Bartaraf etildi", "Yopilgan")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, verbose_name="Tashkilot")
    incident_id = models.CharField("Hodisa ID", max_length=20, blank=True, help_text="Bo‘sh qoldirilsa, avtomatik beriladi.")
    incident_type = models.CharField("Hodisa turi", max_length=60, choices=TYPES)
    severity = models.CharField("Jiddiylik", max_length=10, choices=LEVELS)
    affected_systems = models.CharField("Ta‘sirlangan tizimlar", max_length=300)
    incident_date = models.DateTimeField("Hodisa sanasi")
    description = models.TextField("Tavsif")
    response_actions = models.TextField("Javob choralari", blank=True)
    responsible = models.CharField("Mas‘ul shaxs", max_length=150)
    status = models.CharField("Holati", max_length=20, choices=STATUS, default="Ochiq")

    class Meta:
        ordering = ["-incident_date"]
        verbose_name = "Hodisa"

    def save(self, *a, **kw):
        super().save(*a, **kw)
        if not self.incident_id:
            self.incident_id = f"INC-{self.pk:04d}"
            super().save(update_fields=["incident_id"])

    def __str__(self):
        return self.incident_id or f"Hodisa #{self.pk}"
