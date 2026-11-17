"""PDF (ReportLab) va Excel (openpyxl) hisobotlari."""
from io import BytesIO
from xml.sax.saxutils import escape
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from . import models as m

NAVY = colors.HexColor("#0b1d3a")
CYAN = colors.HexColor("#0891b2")


def _fmt_dt(v):
    return timezone.localtime(v).strftime("%d.%m.%Y %H:%M") if v else "—"


def collect(audit):
    org = audit.organization
    d = dict(
        audit=audit, org=org, items=list(audit.items.all()),
        risks=list(m.Risk.objects.filter(organization=org).select_related("asset")),
        bia=list(m.BIA.objects.filter(organization=org)),
        bcp=list(m.BCPPlan.objects.filter(organization=org)),
        drp=list(m.DRPScenario.objects.filter(organization=org)),
        backups=list(m.Backup.objects.filter(organization=org)),
        incidents=list(m.Incident.objects.filter(organization=org)),
        assets=list(m.Asset.objects.filter(organization=org)),
    )
    d["compliance"] = m.compliance_of(d["items"])
    d["risk_counts"] = {lv: sum(1 for r in d["risks"] if r.level == lv) for lv in ("Kritik", "Yuqori", "O‘rta", "Past")}
    return d


def recommendations(d):
    rec = []
    for r in sorted(d["risks"], key=lambda x: -x.score):
        if r.score >= 10 and r.status not in ("Yopilgan", "Kamaytirilgan") and r.mitigation:
            rec.append(f"[{r.level} xavf, {r.score} ball] {r.threat}: {r.mitigation}")
    for i in d["items"]:
        if i.answer == "Mos emas":
            rec.append(f"[{i.category}] «{i.question}» talabi bajarilmagan — tuzatish choralari ko‘rilsin.")
    for b in d["backups"]:
        if not b.encrypted:
            rec.append(f"Zaxira «{b.name}» shifrlanmagan — shifrlash yoqilsin.")
        if not b.restore_tested:
            rec.append(f"Zaxira «{b.name}» uchun tiklash sinovi o‘tkazilmagan — sinov o‘tkazilib, natijasi qayd etilsin.")
    for p in d["bcp"]:
        if p.approval_status != "Tasdiqlangan":
            rec.append(f"BCP «{p.title}» rasmiy tasdiqlanmagan (holati: {p.approval_status}).")
    return rec


def conclusion_text(d):
    c = d["compliance"]
    if c is None:
        lvl = "Baholash hali yakunlanmagan, shu sababli umumiy muvofiqlik darajasi aniqlanmadi."
    elif c >= 85:
        lvl = f"Muvofiqlik darajasi {c}% — yuqori. Tashkilot nazorat choralari asosan talablarga javob beradi."
    elif c >= 60:
        lvl = f"Muvofiqlik darajasi {c}% — o‘rtacha. Qisman mos va mos bo‘lmagan bandlar bo‘yicha tuzatish chora-tadbirlari zarur."
    else:
        lvl = f"Muvofiqlik darajasi {c}% — past. Zudlik bilan tuzatish dasturini ishlab chiqish tavsiya etiladi."
    txt = audit_note = (d["audit"].conclusion or "").strip()
    out = (txt + "\n\n" if txt else "") + lvl
    out += (" Ushbu hisobot ISO 22301, ISO/IEC 27001/27002/27031, NIST CSF va NIST SP 800-34 standartlariga "
            "tayanch (reference) sifatida asoslangan; u rasmiy sertifikatlash hisoblanmaydi.")
    if d["org"].is_demo:
        out += " DIQQAT: ushbu hisobot DEMO ma‘lumotlar asosida tuzilgan va faqat namoyish uchun mo‘ljallangan."
    return out


def build_pdf(audit, generated_by=None):
    d = collect(audit)
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=16 * mm,
                            bottomMargin=16 * mm, title=f"Audit hisoboti — {audit.title}", author="BCM & DR AUDIT PRO")
    ss = getSampleStyleSheet()
    H1 = ParagraphStyle("H1", parent=ss["Title"], textColor=NAVY, fontSize=22, leading=26)
    H2 = ParagraphStyle("H2", parent=ss["Heading2"], textColor=NAVY, fontSize=13, spaceBefore=12, spaceAfter=6)
    B = ParagraphStyle("B", parent=ss["BodyText"], fontSize=9.5, leading=13)
    S = ParagraphStyle("S", parent=B, fontSize=8, leading=10)
    SH = ParagraphStyle("SH", parent=S, textColor=colors.white, fontName="Helvetica-Bold")
    P = lambda t, st=B: Paragraph(escape(str(t)).replace("\n", "<br/>"), st)

    def tbl(header, rows, widths):
        data = [[Paragraph(escape(h), SH) for h in header]] + [[P(c, S) for c in r] for r in rows]
        t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                               ("VALIGN", (0, 0), (-1, -1), "TOP"), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
                               ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
        return t

    def empty(rows, st):
        st.append(P("Ma‘lumot mavjud emas.") if not rows else Spacer(1, 1))

    s = []
    s += [P("BCM & DR AUDIT PRO", H1),
          P("Biznes uzluksizligi va avariyadan tiklanish xavfsizligi platformasi", ParagraphStyle("c", parent=B, alignment=1, textColor=CYAN, fontSize=11)),
          Spacer(1, 8), P("Axborot xavfsizligi auditi hisoboti", ParagraphStyle("t", parent=H2, alignment=1, fontSize=16)), Spacer(1, 6)]
    if d["org"].is_demo:
        s.append(P("DEMO ma‘lumotlar asosidagi namunaviy hisobot", ParagraphStyle("dm", parent=B, alignment=1, textColor=colors.red)))
    s.append(P("1. Tashkilot va audit ma‘lumotlari", H2))
    o = d["org"]
    s.append(tbl(["Ko‘rsatkich", "Qiymat"], [
        ["Tashkilot", o.name], ["Soha", o.industry], ["Manzil", o.address or "—"],
        ["Mas‘ul shaxs", f"{o.contact_person} ({o.email or '—'})"], ["Xodimlar / serverlar", f"{o.employees} / {o.servers}"],
        ["Audit nomi", audit.title], ["Audit sanasi", audit.audit_date.strftime("%d.%m.%Y")], ["Audit holati", audit.status],
        ["Hisobot yaratilgan", timezone.localtime().strftime("%d.%m.%Y %H:%M")]], [50, 126]))
    s += [P("2. Audit qamrovi", H2), P(audit.scope)]
    rc = d["risk_counts"]
    s.append(P("3. Rahbariyat uchun qisqacha xulosa", H2))
    drp_avg = round(sum(x.progress_pct for x in d["drp"]) / len(d["drp"])) if d["drp"] else 0
    bcp_ok = sum(1 for p in d["bcp"] if p.approval_status == "Tasdiqlangan")
    s.append(P(audit.summary or "")) if audit.summary else None
    s.append(P(f"Audit doirasida {len(d['assets'])} ta axborot aktivi, {len(d['risks'])} ta xavf (kritik: {rc['Kritik']}, yuqori: {rc['Yuqori']}, "
               f"o‘rta: {rc['O‘rta']}, past: {rc['Past']}), {len(d['bcp'])} ta BCP rejasi (tasdiqlangan: {bcp_ok}), {len(d['drp'])} ta DRP stsenariysi "
               f"(o‘rtacha checklist bajarilishi: {drp_avg}%), {len(d['backups'])} ta zaxira nusxa va {len(d['incidents'])} ta hodisa ko‘rib chiqildi. "
               f"Audit savollari bo‘yicha umumiy muvofiqlik: {'—' if d['compliance'] is None else str(d['compliance']) + '%'}."))
    s.append(P("4. Risk baholash (5×5 matritsa)", H2))
    s.append(tbl(["Tahdid", "Aktiv", "E×T", "Ball", "Daraja", "Qoldiq", "Holat"],
                 [[r.threat, r.asset or "—", f"{r.likelihood}×{r.impact}", r.score, r.level, f"{r.residual_score} ({r.residual_level})", r.status]
                  for r in sorted(d["risks"], key=lambda x: -x.score)], [56, 34, 12, 10, 16, 24, 24]))
    empty(d["risks"], s)
    s.append(P("5. BCP baholash", H2))
    s.append(tbl(["Reja", "Mas‘ul", "Qayta ko‘rish", "Holat"], [[p.title, p.responsible, p.review_date.strftime("%d.%m.%Y"), p.approval_status] for p in d["bcp"]], [70, 45, 28, 33]))
    s.append(P("Biznes ta‘sir tahlili (BIA)", ParagraphStyle("h3", parent=B, fontName="Helvetica-Bold", spaceBefore=6)))
    s.append(tbl(["Jarayon", "Muhimlik", "MTD (s)", "RTO (s)", "RPO (s)"], [[b.process, b.criticality, b.mtd_hours, b.rto_hours, b.rpo_hours] for b in d["bia"]], [80, 28, 22, 22, 22]))
    s.append(P("6. DRP baholash", H2))
    s.append(tbl(["Stsenariy", "Ustuvorlik", "Reja (s)", "Fakt (s)", "Checklist", "Holat"],
                 [[x.scenario_type, x.priority, x.estimated_hours, x.actual_hours if x.actual_hours is not None else "—", x.progress, x.status] for x in d["drp"]], [58, 24, 20, 20, 22, 32]))
    s.append(P("7. Zaxira nusxalar baholash", H2))
    s.append(P("Eslatma: «Yaxlitlik» va «Tiklash sinovi» faqat tizimda tasdiqlangan hollarda «Ha» deb ko‘rsatiladi.", S))
    s.append(tbl(["Nomi", "Turi", "Oxirgi", "Shifr", "Yaxlitlik", "Tiklash sinovi", "Holat"],
                 [[b.name, b.backup_type, _fmt_dt(b.last_backup), "Ha" if b.encrypted else "Yo‘q",
                   _fmt_dt(b.integrity_verified_at) if b.integrity_checked else "Tekshirilmagan",
                   _fmt_dt(b.restore_tested_at) if b.restore_tested else "O‘tkazilmagan", b.status] for b in d["backups"]], [38, 20, 25, 12, 28, 28, 25]))
    s.append(P("8. Audit checklist natijalari", H2))
    cats = {}
    for i in d["items"]:
        cats.setdefault(i.category, []).append(i)
    s.append(tbl(["Bo‘lim", "Savollar", "Mos", "Qisman", "Mos emas", "T/E", "Muvofiqlik"],
                 [[c, len(v), sum(i.answer == "Mos" for i in v), sum(i.answer == "Qisman mos" for i in v), sum(i.answer == "Mos emas" for i in v),
                   sum(i.answer == "Tegishli emas" for i in v), "—" if m.compliance_of(v) is None else f"{m.compliance_of(v)}%"] for c, v in cats.items()],
                 [56, 18, 16, 18, 20, 14, 34]))
    s.append(Spacer(1, 6))
    s.append(tbl(["Bo‘lim", "Savol", "Baho", "Izoh / dalil"],
                 [[i.category, i.question, i.answer or "Baholanmagan", (i.comment or "—") + (" [dalil biriktirilgan]" if i.has_evidence else "")] for i in d["items"]], [34, 72, 22, 48]))
    s.append(P("9. Tavsiyalar", H2))
    recs = recommendations(d)
    for i, r in enumerate(recs[:40], 1):
        s.append(P(f"{i}. {r}"))
    if not recs:
        s.append(P("Aniq tavsiyalar mavjud emas."))
    s.append(P("10. Yakuniy xulosa", H2))
    s.append(P(conclusion_text(d)))
    s.append(P("11. Auditor ma‘lumotlari", H2))
    a = audit.auditor
    s.append(tbl(["Ko‘rsatkich", "Qiymat"], [["Auditor", (a.get_full_name() or a.username) if a else "Tayinlanmagan"], ["Lavozim / rol", a.role_label if a else "—"],
                                           ["Hisobotni yaratgan", (generated_by.get_full_name() or generated_by.username) if generated_by else "—"],
                                           ["Imzo", "______________________"]], [50, 126]))

    def footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(16 * mm, 9 * mm, "BCM & DR AUDIT PRO — maxfiy / confidential")
        canvas.drawRightString(A4[0] - 16 * mm, 9 * mm, f"Sahifa {doc_.page}")
        canvas.restoreState()

    doc.build([x for x in s if x is not None], onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()


def build_xlsx(audit):
    d = collect(audit)
    wb = Workbook()
    hdr_fill = PatternFill("solid", fgColor="0B1D3A")

    def sheet(title, header, rows, first=False):
        ws = wb.active if first else wb.create_sheet()
        ws.title = title[:31]
        ws.append(header)
        for c in ws[1]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = hdr_fill
        for r in rows:
            ws.append([str(x) if not isinstance(x, (int, float)) and x is not None else x for x in r])
        for i, col in enumerate(ws.columns, 1):
            w = min(60, max(len(str(c.value or "")) for c in col) + 2)
            ws.column_dimensions[col[0].column_letter].width = max(w, 10)
            for c in col:
                c.alignment = Alignment(wrap_text=True, vertical="top")
        ws.freeze_panes = "A2"

    o = d["org"]
    sheet("Xulosa", ["Ko‘rsatkich", "Qiymat"], [
        ["Dastur", "BCM & DR AUDIT PRO"], ["Tashkilot", o.name], ["Audit", audit.title], ["Audit sanasi", audit.audit_date.strftime("%d.%m.%Y")],
        ["Qamrov", audit.scope], ["Muvofiqlik, %", "—" if d["compliance"] is None else d["compliance"]],
        ["Kritik xavflar", d["risk_counts"]["Kritik"]], ["Yuqori xavflar", d["risk_counts"]["Yuqori"]],
        ["DEMO ma‘lumotmi", "Ha" if o.is_demo else "Yo‘q"], ["Xulosa", conclusion_text(d)]], first=True)
    sheet("Risklar", ["Tahdid", "Zaiflik", "Aktiv", "Egasi", "E", "T", "Ball", "Daraja", "Mavjud nazorat", "Tavsiya", "Qoldiq ball", "Qoldiq daraja", "Holat"],
          [[r.threat, r.vulnerability, r.asset or "", r.owner, r.likelihood, r.impact, r.score, r.level, r.existing_controls, r.mitigation, r.residual_score, r.residual_level, r.status] for r in d["risks"]])
    sheet("BIA", ["Jarayon", "Moliyaviy", "Operatsion", "Huquqiy", "MTD (s)", "RTO (s)", "RPO (s)", "Muhimlik"],
          [[b.process, b.financial_impact, b.operational_impact, b.legal_impact, float(b.mtd_hours), float(b.rto_hours), float(b.rpo_hours), b.criticality] for b in d["bia"]])
    sheet("BCP", ["Reja", "Mas‘ul", "Favqulodda tartib", "Muqobil faoliyat", "Aloqa rejasi", "Qayta ko‘rish", "Holat"],
          [[p.title, p.responsible, p.emergency_procedures, p.alternative_operations, p.communication_plan, p.review_date.strftime("%d.%m.%Y"), p.approval_status] for p in d["bcp"]])
    sheet("DRP", ["Stsenariy", "Tavsif", "Ustuvorlik", "Mas‘ul", "Reja (s)", "Fakt (s)", "Checklist", "Holat"],
          [[x.scenario_type, x.description, x.priority, x.responsible, float(x.estimated_hours), float(x.actual_hours) if x.actual_hours is not None else "", x.progress, x.status] for x in d["drp"]])
    sheet("Zaxira", ["Nomi", "Turi", "Joyi", "Chastota", "Oxirgi", "Hajm GB", "Shifr", "Yaxlitlik tekshiruvi", "Tiklash sinovi", "Holat"],
          [[b.name, b.backup_type, b.storage_location, b.frequency, _fmt_dt(b.last_backup), float(b.size_gb), "Ha" if b.encrypted else "Yo‘q",
            _fmt_dt(b.integrity_verified_at) if b.integrity_checked else "Tekshirilmagan", _fmt_dt(b.restore_tested_at) if b.restore_tested else "O‘tkazilmagan", b.status] for b in d["backups"]])
    sheet("Checklist", ["Bo‘lim", "Savol", "Standart", "Baho", "Izoh", "Dalil"],
          [[i.category, i.question, i.standard_ref, i.answer or "Baholanmagan", i.comment, "Ha" if i.has_evidence else "Yo‘q"] for i in d["items"]])
    sheet("Hodisalar", ["ID", "Turi", "Jiddiylik", "Tizimlar", "Sana", "Mas‘ul", "Holat", "Javob choralari"],
          [[i.incident_id, i.incident_type, i.severity, i.affected_systems, _fmt_dt(i.incident_date), i.responsible, i.status, i.response_actions] for i in d["incidents"]])
    sheet("Tavsiyalar", ["№", "Tavsiya"], [[n, r] for n, r in enumerate(recommendations(d), 1)])
    out = BytesIO()
    wb.save(out)
    return out.getvalue()
