"""Barcha CRUD modullarining yagona tavsifi (ro‘yxat ustunlari, qidiruv, rollar, forma)."""
from django import forms
from accounts.forms import BootstrapMixin, UserForm
from accounts.models import User, ActivityLog
from . import models as m

ALL = ("admin", "auditor", "manager", "viewer")
W_AUD = ("admin", "auditor")
W_OPS = ("admin", "auditor", "manager")

BIA_INTRO = ("<b>RTO</b> (Recovery Time Objective) — uzilishdan keyin jarayon qancha vaqt ichida tiklanishi kerakligi. "
             "<b>RPO</b> (Recovery Point Objective) — ma‘lumotlarning eng ko‘pi bilan qancha vaqtlik qismi yo‘qolishiga yo‘l qo‘yilishi "
             "(zaxira nusxalash oralig‘i RPO dan oshmasligi kerak). <b>MTD</b> — jarayon to‘xtab turishi mumkin bo‘lgan eng uzun muddat; RTO ≤ MTD bo‘lishi shart.")

REGISTRY = {
    "tashkilotlar": dict(model=m.Organization, title="Tashkilotlar", single="Tashkilot", icon="bi-building",
        cols=[("name", "Nomi"), ("industry", "Soha"), ("contact_person", "Mas‘ul shaxs"), ("email", "Email"),
              ("employees", "Xodimlar"), ("servers", "Serverlar")],
        search=["name", "industry", "contact_person"], write=W_AUD, log="Ma‘lumot o‘zgartirish",
        fields=["name", "industry", "address", "contact_person", "email", "employees", "servers", "description"]),
    "aktivlar": dict(model=m.Asset, title="Axborot aktivlari", single="Aktiv", icon="bi-hdd-network",
        cols=[("name", "Nomi"), ("organization", "Tashkilot"), ("asset_type", "Turi"), ("ip_address", "IP"),
              ("criticality", "Muhimlik"), ("owner", "Egasi"), ("protection_status", "Himoya")],
        search=["name", "owner", "ip_address", "asset_type"], filters=["organization"], select=["organization"], write=W_OPS,
        log="Ma‘lumot o‘zgartirish",
        fields=["organization", "name", "asset_type", "ip_address", "criticality", "owner", "protection_status", "description"]),
    "risklar": dict(model=m.Risk, title="Risk baholash", single="Xavf", icon="bi-exclamation-triangle",
        cols=[("threat", "Tahdid"), ("asset", "Aktiv"), ("likelihood", "E"), ("impact", "T"), ("score", "Ball"),
              ("level", "Daraja"), ("residual_level", "Qoldiq"), ("status", "Holati"), ("owner", "Egasi")],
        search=["threat", "vulnerability", "owner", "mitigation"], filters=["organization"], select=["organization", "asset"],
        write=W_AUD, log="Ma‘lumot o‘zgartirish",
        intro="Risk balli = Ehtimollik (E) × Ta‘sir (T). 1–4: Past · 5–9: O‘rta · 10–16: Yuqori · 17–25: Kritik.",
        fields=["organization", "threat", "vulnerability", "asset", "owner", "likelihood", "impact", "existing_controls",
                "mitigation", "residual_likelihood", "residual_impact", "status"]),
    "bia": dict(model=m.BIA, title="Biznes ta‘sir tahlili (BIA)", single="BIA yozuvi", icon="bi-graph-down-arrow",
        cols=[("process", "Biznes jarayon"), ("financial_impact", "Moliyaviy"), ("operational_impact", "Operatsion"),
              ("legal_impact", "Huquqiy"), ("mtd_hours", "MTD (s)"), ("rto_hours", "RTO (s)"), ("rpo_hours", "RPO (s)"),
              ("criticality", "Muhimlik")],
        search=["process"], filters=["organization"], select=["organization"], write=W_OPS, log="Ma‘lumot o‘zgartirish", intro=BIA_INTRO,
        fields=["organization", "process", "financial_impact", "operational_impact", "legal_impact", "mtd_hours",
                "rto_hours", "rpo_hours", "criticality"]),
    "bcp": dict(model=m.BCPPlan, title="Biznes uzluksizligi rejalari (BCP)", single="BCP rejasi", icon="bi-diagram-3",
        cols=[("title", "Reja"), ("organization", "Tashkilot"), ("responsible", "Mas‘ul"), ("review_date", "Qayta ko‘rish"),
              ("approval_status", "Holati")],
        search=["title", "responsible"], filters=["organization"], select=["organization"], write=W_OPS, log="Ma‘lumot o‘zgartirish",
        fields=["organization", "title", "responsible", "emergency_procedures", "alternative_operations",
                "communication_plan", "review_date", "approval_status"]),
    "drp": dict(model=m.DRPScenario, title="Avariyadan tiklash stsenariylari (DRP)", single="DRP stsenariysi", icon="bi-arrow-repeat",
        cols=[("scenario_type", "Stsenariy"), ("priority", "Ustuvorlik"), ("responsible", "Mas‘ul"),
              ("estimated_hours", "Reja (s)"), ("actual_hours", "Fakt (s)"), ("progress", "Checklist"), ("status", "Holati")],
        search=["scenario_type", "description", "responsible"], filters=["organization"], select=["organization"], write=W_OPS,
        detail="drp_detail", log="Ma‘lumot o‘zgartirish", after="sync_steps",
        fields=["organization", "scenario_type", "description", "priority", "recovery_steps", "responsible",
                "estimated_hours", "actual_hours", "status"]),
    "zaxira": dict(model=m.Backup, title="Zaxira nusxalar monitoringi", single="Zaxira nusxa", icon="bi-cloud-arrow-up",
        cols=[("name", "Nomi"), ("backup_type", "Turi"), ("storage_location", "Joyi"), ("frequency", "Chastota"),
              ("last_backup", "Oxirgi"), ("size_gb", "GB"), ("encrypted", "Shifr"), ("integrity_checked", "Yaxlitlik"),
              ("restore_tested", "Tiklash sinovi"), ("status", "Holati")],
        search=["name", "storage_location"], filters=["organization"], select=["organization"], write=W_OPS,
        detail="backup_detail", log="Zaxira",
        intro="«Yaxlitlik» va «Tiklash sinovi» ustunlari faqat foydalanuvchi tekshiruvni haqiqatan bajarib, tizimda tasdiqlagandan so‘ng «Ha» bo‘ladi.",
        fields=["organization", "name", "backup_type", "storage_location", "frequency", "last_backup", "next_backup",
                "size_gb", "encrypted", "status"]),
    "auditlar": dict(model=m.Audit, title="Axborot xavfsizligi auditlari", single="Audit", icon="bi-clipboard-check",
        cols=[("title", "Audit"), ("organization", "Tashkilot"), ("audit_date", "Sana"), ("status", "Holati"),
              ("auditor", "Auditor"), ("compliance_text", "Muvofiqlik")],
        search=["title", "scope"], filters=["organization"], select=["organization", "auditor"], write=W_AUD,
        detail="audit_detail", log="Audit",
        fields=["organization", "title", "scope", "audit_date", "status", "auditor", "summary", "conclusion"]),
    "tekshiruv": dict(model=m.ChecklistItem, title="Audit savollari (checklist)", single="Audit savoli", icon="bi-card-checklist",
        cols=[("audit", "Audit"), ("category", "Bo‘lim"), ("question", "Savol"), ("standard_ref", "Standart"),
              ("answer", "Baho"), ("has_evidence", "Dalil")],
        search=["question", "category", "comment"], filters=["audit"], select=["audit"], write=W_AUD, log="Audit",
        intro="Barcha savollarni bir sahifada baholash uchun «Auditlar» → audit sahifasi → «Baholashni to‘ldirish» tugmasidan foydalaning.",
        fields=["audit", "category", "question", "standard_ref", "answer", "comment", "evidence"]),
    "hodisalar": dict(model=m.Incident, title="Hodisalarni boshqarish", single="Hodisa", icon="bi-shield-exclamation",
        cols=[("incident_id", "ID"), ("incident_type", "Turi"), ("severity", "Jiddiylik"), ("affected_systems", "Tizimlar"),
              ("incident_date", "Sana"), ("responsible", "Mas‘ul"), ("status", "Holati")],
        search=["incident_id", "description", "affected_systems", "responsible"], filters=["organization"],
        select=["organization"], write=W_OPS, log="Hodisa",
        fields=["organization", "incident_id", "incident_type", "severity", "affected_systems", "incident_date",
                "description", "response_actions", "responsible", "status"]),
    "jurnal": dict(model=ActivityLog, title="Faoliyat jurnali", single="Yozuv", icon="bi-clock-history",
        cols=[("created_at", "Vaqt"), ("user", "Foydalanuvchi"), ("category", "Turi"), ("message", "Tavsif"), ("ip", "IP")],
        search=["message", "category", "user__username"], select=["user"], write=(), read=W_AUD, fields=[]),
    "foydalanuvchilar": dict(model=User, title="Foydalanuvchilar", single="Foydalanuvchi", icon="bi-people",
        cols=[("username", "Login"), ("get_full_name", "F.I.Sh."), ("email", "Email"), ("role_label", "Rol"),
              ("is_active", "Faol"), ("last_login", "Oxirgi kirish")],
        search=["username", "first_name", "last_name", "email"], write=("admin",), read=("admin",), form=UserForm,
        log="Foydalanuvchi faoliyati", fields=[]),
}
for _k, _c in REGISTRY.items():
    _c.setdefault("read", ALL)
    _c.setdefault("filters", [])
    _c.setdefault("select", [])
    _c["key"] = _k


def make_form(cfg):
    if cfg.get("form"):
        return cfg["form"]

    class F(BootstrapMixin, forms.ModelForm):
        class Meta:
            model = cfg["model"]
            fields = cfg["fields"]
    return F
