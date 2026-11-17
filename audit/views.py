import json
from datetime import date, datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.utils import log
from . import models as m
from .registry import REGISTRY, make_form
from . import reports

BADGE = {
    "Kritik": "danger", "Yuqori": "warning", "O‘rta": "info", "Past": "success",
    "Muvaffaqiyatli": "success", "Xatolik": "danger", "Kutilmoqda": "secondary", "Tekshirish kerak": "warning",
    "Mos": "success", "Qisman mos": "warning", "Mos emas": "danger", "Tegishli emas": "secondary",
    "Ochiq": "danger", "Tekshirilmoqda": "warning", "Bartaraf etildi": "success", "Yopilgan": "secondary",
    "Tasdiqlangan": "success", "Qoralama": "secondary", "Ko‘rib chiqilmoqda": "info", "Muddati o‘tgan": "danger",
    "Tiklandi": "success", "Jarayonda": "primary", "Rejalashtirilgan": "secondary", "Muvaffaqiyatsiz": "danger",
    "Himoyalangan": "success", "Qisman himoyalangan": "warning", "Himoyalanmagan": "danger",
    "Kamaytirilgan": "success", "Qabul qilingan": "info", "Yakunlangan": "success",
}


def cell(o, a):
    v = getattr(o, a)
    if callable(v):
        v = v()
    d = getattr(o, f"get_{a}_display", None)
    if d:
        v = d()
    if v is None or v == "":
        return ("—", None)
    if isinstance(v, bool):
        return ("Ha" if v else "Yo‘q", "success" if v else "secondary")
    if isinstance(v, datetime):
        return (timezone.localtime(v).strftime("%d.%m.%Y %H:%M"), None)
    if isinstance(v, date):
        return (v.strftime("%d.%m.%Y"), None)
    s = str(v)
    return (s if len(s) <= 70 else s[:67] + "…", BADGE.get(s))


def get_cfg(key):
    cfg = REGISTRY.get(key)
    if not cfg:
        raise Http404
    return cfg


def need(request, key, write=False):
    cfg = get_cfg(key)
    role = request.user.role_key
    if role not in cfg["read"] or (write and role not in cfg["write"]):
        raise PermissionDenied
    return cfg


def can(request, key):
    return request.user.role_key in REGISTRY[key]["write"]


# ---------------------------------------------------------------- CRUD
@login_required
def crud_list(request, key):
    cfg = need(request, key)
    qs = cfg["model"].objects.all()
    if cfg["select"]:
        qs = qs.select_related(*cfg["select"])
    q = request.GET.get("q", "").strip()
    if q:
        cond = Q()
        for f in cfg["search"]:
            cond |= Q(**{f + "__icontains": q})
        qs = qs.filter(cond)
    flt = {}
    for f in cfg["filters"]:
        v = request.GET.get(f, "")
        if v.isdigit():
            qs = qs.filter(**{f: int(v)})
        flt[f] = v
    if not qs.ordered:
        qs = qs.order_by("pk")
    page = Paginator(qs, 10).get_page(request.GET.get("page"))
    rows = [{"obj": o, "cells": [cell(o, a) for a, _ in cfg["cols"]]} for o in page]
    params = request.GET.copy()
    params.pop("page", None)
    filter_opts = []
    if "organization" in cfg["filters"]:
        filter_opts.append(("organization", "Barcha tashkilotlar", m.Organization.objects.all(), flt["organization"]))
    if "audit" in cfg["filters"]:
        filter_opts.append(("audit", "Barcha auditlar", m.Audit.objects.all(), flt["audit"]))
    return render(request, "list.html", dict(
        cfg=cfg, key=key, page=page, rows=rows, q=q, qs_extra=params.urlencode(), filter_opts=filter_opts,
        can_write=can(request, key), crumbs=[("Boshqaruv paneli", "/"), (cfg["title"], None)]))


@login_required
def crud_form(request, key, pk=None):
    cfg = need(request, key, write=True)
    obj = get_object_or_404(cfg["model"], pk=pk) if pk else None
    Form = make_form(cfg)
    initial = {k: v for k, v in request.GET.items() if k in Form.base_fields} if not obj else None
    form = Form(request.POST or None, request.FILES or None, instance=obj, initial=initial)
    if request.method == "POST" and form.is_valid():
        o = form.save()
        if cfg.get("after"):
            getattr(o, cfg["after"])()
        log(request.user, cfg["log"], f"{cfg['single']} {'yangilandi' if pk else 'yaratildi'}: {o}", request)
        messages.success(request, f"{cfg['single']} muvaffaqiyatli {'yangilandi' if pk else 'saqlandi'}.")
        nxt = cfg.get("detail")
        if nxt and key in ("auditlar",) and not pk:
            return redirect(nxt, pk=o.pk)
        return redirect("list", key=key)
    elif request.method == "POST":
        messages.error(request, "Formada xatolar bor. Iltimos, belgilangan maydonlarni tuzating.")
    return render(request, "form.html", dict(
        cfg=cfg, key=key, form=form, obj=obj, can_write=True,
        crumbs=[("Boshqaruv paneli", "/"), (cfg["title"], f"/{key}/"), ("Tahrirlash" if pk else "Yangi yozuv", None)]))


@login_required
def crud_delete(request, key, pk):
    cfg = need(request, key, write=True)
    obj = get_object_or_404(cfg["model"], pk=pk)
    if key == "foydalanuvchilar" and obj.pk == request.user.pk:
        messages.error(request, "O‘zingizning hisobingizni o‘chira olmaysiz.")
        return redirect("list", key=key)
    if request.method == "POST":
        name = str(obj)
        obj.delete()
        log(request.user, cfg["log"], f"{cfg['single']} o‘chirildi: {name}", request)
        messages.success(request, f"{cfg['single']} o‘chirildi.")
        return redirect("list", key=key)
    return render(request, "confirm_delete.html", dict(
        cfg=cfg, key=key, obj=obj, crumbs=[("Boshqaruv paneli", "/"), (cfg["title"], f"/{key}/"), ("O‘chirish", None)]))


# ---------------------------------------------------------------- Dashboard
def dashboard_data():
    risks = list(m.Risk.objects.all())
    items = m.ChecklistItem.objects.all()
    levels = ["Kritik", "Yuqori", "O‘rta", "Past"]
    rc = {lv: sum(1 for r in risks if r.level == lv) for lv in levels}
    drps = list(m.DRPScenario.objects.all())
    bcps = m.BCPPlan.objects.all()
    bcp_total = bcps.count()
    bcp_ready = round(bcps.filter(approval_status="Tasdiqlangan").count() / bcp_total * 100) if bcp_total else 0
    steps = m.DRPStep.objects.all()
    st_total = steps.count()
    drp_ready = round(steps.filter(done=True).count() / st_total * 100) if st_total else 0
    bk = {s: m.Backup.objects.filter(status=s).count() for s, _ in m.Backup.STATUS}
    ans = {a: items.filter(answer=a).count() for a, _ in m.ChecklistItem.ANSWERS}
    inc = {s: m.Incident.objects.filter(severity=s).count() for s in levels}
    return dict(
        stats=dict(orgs=m.Organization.objects.count(), active_audits=m.Audit.objects.filter(status="Jarayonda").count(),
                   risks=len(risks), critical=rc["Kritik"], bcp=bcp_ready, drp=drp_ready,
                   backup_ok=bk["Muvaffaqiyatli"], backup_total=sum(bk.values()),
                   open_incidents=m.Incident.objects.filter(status__in=["Ochiq", "Tekshirilmoqda"]).count(),
                   compliance=m.compliance_of(items)),
        charts=dict(risk=dict(labels=levels, data=[rc[l] for l in levels]),
                    audit=dict(labels=list(ans), data=list(ans.values())),
                    backup=dict(labels=list(bk), data=list(bk.values())),
                    incident=dict(labels=levels, data=[inc[l] for l in levels]),
                    ready=dict(labels=["BCP tayyorgarligi", "DRP tayyorgarligi"], data=[bcp_ready, drp_ready])))


@login_required
def dashboard(request):
    d = dashboard_data()
    recent = m.Incident.objects.exclude(status="Yopilgan")[:5]
    top_risks = sorted(m.Risk.objects.select_related("asset"), key=lambda r: -r.score)[:5]
    return render(request, "dashboard.html", dict(stats=d["stats"], charts=d["charts"], recent=recent, top_risks=top_risks,
                                                  demo=m.Organization.objects.filter(is_demo=True).exists(),
                                                  crumbs=[("Boshqaruv paneli", None)]))


# ---------------------------------------------------------------- Risk matritsasi
@login_required
def risk_matrix(request):
    residual = request.GET.get("tur") == "qoldiq"
    org = request.GET.get("org", "")
    qs = m.Risk.objects.select_related("asset")
    if org.isdigit():
        qs = qs.filter(organization_id=int(org))
    cells = {}
    for r in qs:
        k = (r.residual_likelihood, r.residual_impact) if residual else (r.likelihood, r.impact)
        cells.setdefault(k, []).append(r)
    grid = []
    for imp in range(5, 0, -1):
        row = []
        for lik in range(1, 6):
            sc = lik * imp
            lv = m.risk_level(sc)
            rs = cells.get((lik, imp), [])
            row.append(dict(score=sc, level=lv, key=m.LEVEL_KEY[lv], risks=rs, count=len(rs)))
        grid.append((imp, row))
    return render(request, "matrix.html", dict(grid=grid, residual=residual, org=org, orgs=m.Organization.objects.all(),
                                               total=sum(len(v) for v in cells.values()),
                                               crumbs=[("Boshqaruv paneli", "/"), ("Risk baholash", "/risklar/"), ("Risk matritsasi", None)]))


# ---------------------------------------------------------------- DRP
@login_required
def drp_detail(request, pk):
    need(request, "drp")
    sc = get_object_or_404(m.DRPScenario, pk=pk)
    return render(request, "drp_detail.html", dict(sc=sc, steps=sc.steps.all(), can_write=can(request, "drp"),
                                                   crumbs=[("Boshqaruv paneli", "/"), ("DRP", "/drp/"), (str(sc), None)]))


@login_required
@require_POST
def drp_step(request, pk, sid):
    need(request, "drp", write=True)
    st = get_object_or_404(m.DRPStep, pk=sid, scenario_id=pk)
    st.done = not st.done
    st.save(update_fields=["done"])
    log(request.user, "Ma‘lumot o‘zgartirish", f"DRP bosqichi {'bajarildi' if st.done else 'bekor qilindi'}: {st.text[:80]}", request)
    return JsonResponse({"done": st.done, "percent": st.scenario.progress_pct})


# ---------------------------------------------------------------- Zaxira
@login_required
def backup_detail(request, pk):
    need(request, "zaxira")
    b = get_object_or_404(m.Backup, pk=pk)
    return render(request, "backup_detail.html", dict(b=b, can_write=can(request, "zaxira"),
                                                      crumbs=[("Boshqaruv paneli", "/"), ("Zaxira nusxalar", "/zaxira/"), (b.name, None)]))


@login_required
@require_POST
def backup_confirm(request, pk, kind):
    need(request, "zaxira", write=True)
    b = get_object_or_404(m.Backup, pk=pk)
    who = request.user.get_full_name() or request.user.username
    if kind == "yaxlitlik":
        b.integrity_verified_at, b.integrity_verified_by = timezone.now(), who
        what = "yaxlitlik tekshiruvi"
    elif kind == "tiklash":
        b.restore_tested_at, b.restore_tested_by = timezone.now(), who
        what = "tiklash sinovi"
    else:
        raise Http404
    b.save()
    log(request.user, "Zaxira", f"«{b.name}» uchun {what} bajarilgani tasdiqlandi", request)
    messages.success(request, f"{what.capitalize()} bajarilgani qayd etildi ({who}).")
    return redirect("backup_detail", pk=pk)


# ---------------------------------------------------------------- Audit
@login_required
def audit_detail(request, pk):
    need(request, "auditlar")
    a = get_object_or_404(m.Audit.objects.select_related("organization", "auditor"), pk=pk)
    items = list(a.items.all())
    cats = []
    for c, _ in m.ChecklistItem.CATEGORIES:
        v = [i for i in items if i.category == c]
        if v:
            cats.append(dict(name=c, n=len(v), pct=m.compliance_of(v), items=v))
    counts = {x: sum(1 for i in items if i.answer == x) for x, _ in m.ChecklistItem.ANSWERS}
    counts["Baholanmagan"] = sum(1 for i in items if not i.answer)
    return render(request, "audit_detail.html", dict(a=a, cats=cats, counts=counts, compliance=a.compliance,
                                                     can_write=can(request, "auditlar"),
                                                     crumbs=[("Boshqaruv paneli", "/"), ("Auditlar", "/auditlar/"), (a.title, None)]))


@login_required
def audit_fill(request, pk):
    need(request, "tekshiruv", write=True)
    a = get_object_or_404(m.Audit, pk=pk)
    items = list(a.items.all())
    if request.method == "POST":
        valid = {x for x, _ in m.ChecklistItem.ANSWERS}
        n = 0
        for i in items:
            ans = request.POST.get(f"a_{i.pk}", "")
            com = request.POST.get(f"c_{i.pk}", "").strip()
            if ans in valid or ans == "":
                if ans != i.answer or com != i.comment:
                    i.answer, i.comment = ans, com
                    i.save(update_fields=["answer", "comment", "updated_at"])
                    n += 1
        log(request.user, "Audit", f"«{a.title}» audit baholari saqlandi ({n} ta o‘zgarish)", request)
        messages.success(request, f"Baholar saqlandi. Muvofiqlik: {a.compliance_text}")
        return redirect("audit_detail", pk=pk)
    groups = []
    for c, _ in m.ChecklistItem.CATEGORIES:
        v = [i for i in items if i.category == c]
        if v:
            groups.append((c, v))
    return render(request, "audit_fill.html", dict(a=a, groups=groups, answers=[x for x, _ in m.ChecklistItem.ANSWERS],
                                                   crumbs=[("Boshqaruv paneli", "/"), ("Auditlar", "/auditlar/"), (a.title, f"/auditlar/{a.pk}/"), ("Baholash", None)]))


@login_required
def evidence_download(request, pk):
    i = get_object_or_404(m.ChecklistItem, pk=pk)
    if not i.evidence:
        raise Http404
    return FileResponse(i.evidence.open("rb"), as_attachment=True, filename=i.evidence.name.split("/")[-1])


# ---------------------------------------------------------------- Hisobotlar
@login_required
def reports_index(request):
    return render(request, "reports.html", dict(audits=m.Audit.objects.select_related("organization"),
                                                crumbs=[("Boshqaruv paneli", "/"), ("Hisobotlar", None)]))


@login_required
def report_pdf(request, pk):
    a = get_object_or_404(m.Audit, pk=pk)
    data = reports.build_pdf(a, request.user)
    log(request.user, "Hisobot", f"PDF hisobot yaratildi: {a.title}", request)
    r = HttpResponse(data, content_type="application/pdf")
    r["Content-Disposition"] = f'attachment; filename="audit_hisobot_{a.pk}.pdf"'
    return r


@login_required
def report_xlsx(request, pk):
    a = get_object_or_404(m.Audit, pk=pk)
    data = reports.build_xlsx(a)
    log(request.user, "Hisobot", f"Excel hisobot yaratildi: {a.title}", request)
    r = HttpResponse(data, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    r["Content-Disposition"] = f'attachment; filename="audit_hisobot_{a.pk}.xlsx"'
    return r


@login_required
def standards(request):
    return render(request, "standards.html", dict(crumbs=[("Boshqaruv paneli", "/"), ("Standartlar", None)]))
