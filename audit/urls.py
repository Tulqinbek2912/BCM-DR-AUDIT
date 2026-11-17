from django.urls import path, re_path
from . import views as v
from .registry import REGISTRY

keys = "|".join(REGISTRY)
urlpatterns = [
    path("", v.dashboard, name="dashboard"),
    path("risklar/matritsa/", v.risk_matrix, name="risk_matrix"),
    path("drp/<int:pk>/", v.drp_detail, name="drp_detail"),
    path("drp/<int:pk>/qadam/<int:sid>/", v.drp_step, name="drp_step"),
    path("zaxira/<int:pk>/", v.backup_detail, name="backup_detail"),
    path("zaxira/<int:pk>/tasdiqlash/<str:kind>/", v.backup_confirm, name="backup_confirm"),
    path("auditlar/<int:pk>/", v.audit_detail, name="audit_detail"),
    path("auditlar/<int:pk>/baholash/", v.audit_fill, name="audit_fill"),
    path("hisobotlar/", v.reports_index, name="reports"),
    path("hisobotlar/<int:pk>/pdf/", v.report_pdf, name="report_pdf"),
    path("hisobotlar/<int:pk>/xlsx/", v.report_xlsx, name="report_xlsx"),
    path("dalil/<int:pk>/", v.evidence_download, name="evidence"),
    path("standartlar/", v.standards, name="standards"),
    re_path(rf"^(?P<key>{keys})/$", v.crud_list, name="list"),
    re_path(rf"^(?P<key>{keys})/yangi/$", v.crud_form, name="add"),
    re_path(rf"^(?P<key>{keys})/(?P<pk>\d+)/tahrirlash/$", v.crud_form, name="edit"),
    re_path(rf"^(?P<key>{keys})/(?P<pk>\d+)/ochirish/$", v.crud_delete, name="delete"),
]
