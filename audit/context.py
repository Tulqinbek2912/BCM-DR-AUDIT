from django.urls import reverse

# (nom, url, ikonka, ruxsat etilgan rollar yoki None)
def nav(request):
    u = getattr(request, "user", None)
    if not u or not u.is_authenticated:
        return {}
    L = lambda k: reverse("list", args=[k])
    sections = [
        ("Umumiy", [("Boshqaruv paneli", reverse("dashboard"), "bi-speedometer2", None)]),
        ("Ob‘ektlar", [("Tashkilotlar", L("tashkilotlar"), "bi-building", None),
                       ("Axborot aktivlari", L("aktivlar"), "bi-hdd-network", None)]),
        ("Xavflar va ta‘sir", [("Risk baholash", L("risklar"), "bi-exclamation-triangle", None),
                               ("Risk matritsasi 5×5", reverse("risk_matrix"), "bi-grid-3x3-gap", None),
                               ("BIA tahlili", L("bia"), "bi-graph-down-arrow", None)]),
        ("Uzluksizlik va tiklash", [("BCP rejalari", L("bcp"), "bi-diagram-3", None),
                                    ("DRP stsenariylari", L("drp"), "bi-arrow-repeat", None),
                                    ("Zaxira nusxalar", L("zaxira"), "bi-cloud-arrow-up", None)]),
        ("Audit", [("Auditlar", L("auditlar"), "bi-clipboard-check", None),
                   ("Audit savollari", L("tekshiruv"), "bi-card-checklist", None),
                   ("Hodisalar", L("hodisalar"), "bi-shield-exclamation", None),
                   ("Hisobotlar", reverse("reports"), "bi-file-earmark-bar-graph", None),
                   ("Standartlar", reverse("standards"), "bi-journal-bookmark", None)]),
        ("Boshqaruv", [("Faoliyat jurnali", L("jurnal"), "bi-clock-history", ("admin", "auditor")),
                       ("Foydalanuvchilar", L("foydalanuvchilar"), "bi-people", ("admin",))]),
    ]
    role = u.role_key
    menu = []
    for title, items in sections:
        its = [(n, url, ic, request.path == url or (url != "/" and request.path.startswith(url)))
               for n, url, ic, roles in items if roles is None or role in roles]
        if its:
            menu.append((title, its))
    return {"menu": menu, "role_label": u.role_label, "role_key": role}
