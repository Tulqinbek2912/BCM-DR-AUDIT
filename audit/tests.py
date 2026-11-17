from datetime import date
from io import BytesIO
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from accounts.models import User, ActivityLog
from . import models as m


class Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)
        cls.admin = User.objects.get(username="admin")
        cls.admin.must_change_password = False
        cls.admin.save()
        cls.auditor = User.objects.get(username="auditor_demo")
        cls.manager = User.objects.get(username="menejer_demo")
        cls.viewer = User.objects.get(username="kuzatuvchi_demo")
        cls.org = m.Organization.objects.get(is_demo=True)


class StartupAndAuth(Base):
    def test_login_required(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/kirish/", r["Location"])

    def test_login_and_log(self):
        self.assertTrue(self.client.login(username="auditor_demo", password="Demo#2026Pass"))
        r = self.client.post(reverse("login"), {"username": "auditor_demo", "password": "Demo#2026Pass"})
        self.assertEqual(r.status_code, 302)
        self.client.logout()
        self.client.post(reverse("login"), {"username": "x", "password": "bad"})
        self.assertTrue(ActivityLog.objects.filter(category="Kirish", message__contains="Muvaffaqiyatsiz").exists())

    def test_force_password_change(self):
        self.client.login(username="admin", password="Admin#2026Demo")
        u = User.objects.get(username="admin")
        u.must_change_password = True
        u.save()
        self.assertRedirects(self.client.get("/"), reverse("password_change"))
        r = self.client.post(reverse("password_change"), {"old_password": "Admin#2026Demo", "new_password1": "Yangi#Parol2026x", "new_password2": "Yangi#Parol2026x"})
        self.assertEqual(r.status_code, 302)
        u.refresh_from_db()
        self.assertFalse(u.must_change_password)
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_pages_render_for_admin(self):
        self.client.force_login(self.admin)
        for name in ["", "risklar/matritsa/", "hisobotlar/", "standartlar/", "risklar/matritsa/?tur=qoldiq"]:
            self.assertEqual(self.client.get("/" + name).status_code, 200, name)
        for key in ["tashkilotlar", "aktivlar", "risklar", "bia", "bcp", "drp", "zaxira", "auditlar", "tekshiruv", "hodisalar", "jurnal", "foydalanuvchilar"]:
            self.assertEqual(self.client.get(f"/{key}/").status_code, 200, key)
            self.assertEqual(self.client.get(f"/{key}/?q=a&page=1").status_code, 200)
        for key in ["tashkilotlar", "aktivlar", "risklar", "bia", "bcp", "drp", "zaxira", "auditlar", "tekshiruv", "hodisalar", "foydalanuvchilar"]:
            self.assertEqual(self.client.get(f"/{key}/yangi/").status_code, 200, key)


class Permissions(Base):
    def test_viewer_readonly(self):
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get("/tashkilotlar/").status_code, 200)
        self.assertEqual(self.client.get("/tashkilotlar/yangi/").status_code, 403)
        self.assertEqual(self.client.post("/aktivlar/yangi/", {}).status_code, 403)
        self.assertEqual(self.client.get("/jurnal/").status_code, 403)
        self.assertEqual(self.client.get("/foydalanuvchilar/").status_code, 403)

    def test_manager_scope(self):
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get("/bcp/yangi/").status_code, 200)
        self.assertEqual(self.client.get("/risklar/yangi/").status_code, 403)
        self.assertEqual(self.client.get("/foydalanuvchilar/").status_code, 403)

    def test_auditor_cannot_manage_users(self):
        self.client.force_login(self.auditor)
        self.assertEqual(self.client.get("/foydalanuvchilar/").status_code, 403)
        self.assertEqual(self.client.get("/jurnal/").status_code, 200)


class CRUD(Base):
    def test_asset_cycle(self):
        self.client.force_login(self.auditor)
        data = dict(organization=self.org.pk, name="Test aktiv", asset_type="Server", ip_address="10.0.0.9", criticality="Yuqori",
                    owner="Ega", protection_status="Himoyalangan", description="")
        r = self.client.post("/aktivlar/yangi/", data)
        self.assertEqual(r.status_code, 302)
        a = m.Asset.objects.get(name="Test aktiv")
        data["name"] = "Test aktiv 2"
        self.assertEqual(self.client.post(f"/aktivlar/{a.pk}/tahrirlash/", data).status_code, 302)
        a.refresh_from_db()
        self.assertEqual(a.name, "Test aktiv 2")
        self.assertEqual(self.client.get(f"/aktivlar/{a.pk}/ochirish/").status_code, 200)
        self.client.post(f"/aktivlar/{a.pk}/ochirish/")
        self.assertFalse(m.Asset.objects.filter(pk=a.pk).exists())
        self.assertTrue(ActivityLog.objects.filter(message__contains="Test aktiv").exists())

    def test_validation_errors(self):
        self.client.force_login(self.auditor)
        r = self.client.post("/risklar/yangi/", dict(organization=self.org.pk, threat="T", vulnerability="V", owner="o", likelihood=9, impact=3,
                                                     residual_likelihood=1, residual_impact=1, status="Ochiq"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "text-danger")

    def test_bia_rto_le_mtd(self):
        self.client.force_login(self.auditor)
        d = dict(organization=self.org.pk, process="P", financial_impact="Past", operational_impact="Past", legal_impact="Past",
                 mtd_hours=2, rto_hours=5, rpo_hours=1, criticality="Past")
        self.assertEqual(self.client.post("/bia/yangi/", d).status_code, 200)
        d["rto_hours"] = 1
        self.assertEqual(self.client.post("/bia/yangi/", d).status_code, 302)

    def test_user_create(self):
        self.client.force_login(self.admin)
        r = self.client.post("/foydalanuvchilar/yangi/", dict(username="yangi", role="viewer", is_active="on", password="Kuchli#Parol77"))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(User.objects.get(username="yangi").check_password("Kuchli#Parol77"))


class Calculations(Base):
    def test_risk_levels(self):
        for s, lv in [(1, "Past"), (4, "Past"), (5, "O‘rta"), (9, "O‘rta"), (10, "Yuqori"), (16, "Yuqori"), (17, "Kritik"), (25, "Kritik")]:
            self.assertEqual(m.risk_level(s), lv)
        r = m.Risk(likelihood=4, impact=5, residual_likelihood=2, residual_impact=2)
        self.assertEqual((r.score, r.level, r.residual_score, r.residual_level), (20, "Kritik", 4, "Past"))

    def test_compliance(self):
        a = m.Audit.objects.create(organization=self.org, title="T", scope="s", audit_date=date.today())
        for ans in ["Mos", "Qisman mos", "Mos emas", "Tegishli emas", ""]:
            m.ChecklistItem.objects.create(audit=a, category="BCP va DRP", question="q", answer=ans)
        self.assertEqual(a.compliance, 50.0)  # (1+0.5+0)/3
        self.assertIsNone(m.Audit.objects.create(organization=self.org, title="E", scope="s", audit_date=date.today()).compliance)

    def test_audit_fill_updates_compliance(self):
        self.client.force_login(self.auditor)
        a = m.Audit.objects.create(organization=self.org, title="F", scope="s", audit_date=date.today())
        i = m.ChecklistItem.objects.create(audit=a, category="BCP va DRP", question="q")
        self.client.post(f"/auditlar/{a.pk}/baholash/", {f"a_{i.pk}": "Mos", f"c_{i.pk}": "yaxshi"})
        i.refresh_from_db()
        self.assertEqual((i.answer, i.comment, a.compliance), ("Mos", "yaxshi", 100.0))

    def test_dashboard_is_database_driven(self):
        self.client.force_login(self.admin)
        r = self.client.get("/")
        st = r.context["stats"]
        self.assertEqual((st["orgs"], st["risks"], st["backup_total"]), (1, 15, 5))
        m.Risk.objects.create(organization=self.org, threat="Yangi", vulnerability="v", owner="o", likelihood=5, impact=5)
        self.assertEqual(self.client.get("/").context["stats"]["risks"], 16)
        self.assertEqual(self.client.get("/").context["stats"]["critical"], st["critical"] + 1)

    def test_matrix_counts(self):
        self.client.force_login(self.admin)
        r = self.client.get("/risklar/matritsa/")
        self.assertEqual(r.context["total"], 15)
        self.assertEqual(len(r.context["grid"]), 5)

    def test_seed_idempotent(self):
        call_command("seed_demo", verbosity=0)
        self.assertEqual(m.Risk.objects.count(), 15)


class BCPDRPBackup(Base):
    def test_drp_steps_sync_and_toggle(self):
        self.client.force_login(self.manager)
        sc = m.DRPScenario.objects.get(scenario_type="Ransomware (to‘lov dasturi)")
        self.assertEqual(sc.steps.count(), 6)
        st = sc.steps.first()
        r = self.client.post(f"/drp/{sc.pk}/qadam/{st.pk}/")
        self.assertEqual(r.json(), {"done": True, "percent": 17})
        sc.recovery_steps = "A\nB"
        sc.save()
        sc.sync_steps()
        self.assertEqual(sc.steps.count(), 2)

    def test_viewer_cannot_toggle(self):
        self.client.force_login(self.viewer)
        sc = m.DRPScenario.objects.first()
        self.assertEqual(self.client.post(f"/drp/{sc.pk}/qadam/{sc.steps.first().pk}/").status_code, 403)

    def test_backup_not_verified_by_default_and_confirm(self):
        b = m.Backup.objects.first()
        self.assertFalse(b.integrity_checked or b.restore_tested)
        self.client.force_login(self.auditor)
        self.client.post(f"/zaxira/{b.pk}/tasdiqlash/yaxlitlik/")
        b.refresh_from_db()
        self.assertTrue(b.integrity_checked)
        self.assertEqual(b.integrity_verified_by, "Auditor Demo")
        self.assertFalse(b.restore_tested)

    def test_bcp_readiness(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get("/").context["stats"]["bcp"], 40)  # 2 / 5 tasdiqlangan


class Reports(Base):
    def setUp(self):
        self.client.force_login(self.admin)
        self.audit = m.Audit.objects.get(is_demo=True)

    def test_pdf(self):
        r = self.client.get(f"/hisobotlar/{self.audit.pk}/pdf/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "application/pdf")
        self.assertTrue(r.content.startswith(b"%PDF"))
        self.assertTrue(ActivityLog.objects.filter(category="Hisobot").exists())

    def test_xlsx(self):
        r = self.client.get(f"/hisobotlar/{self.audit.pk}/xlsx/")
        self.assertEqual(r.status_code, 200)
        from openpyxl import load_workbook
        wb = load_workbook(BytesIO(r.content))
        self.assertIn("Risklar", wb.sheetnames)
        self.assertEqual(wb["Risklar"].max_row, 16)
        self.assertEqual(wb["Checklist"].max_row, 21)

    def test_audit_detail_page(self):
        self.assertEqual(self.client.get(f"/auditlar/{self.audit.pk}/").status_code, 200)
        self.assertEqual(self.client.get(f"/auditlar/{self.audit.pk}/baholash/").status_code, 200)
        self.assertEqual(self.client.get(f"/drp/{m.DRPScenario.objects.first().pk}/").status_code, 200)
        self.assertEqual(self.client.get(f"/zaxira/{m.Backup.objects.first().pk}/").status_code, 200)
