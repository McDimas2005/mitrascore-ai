from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from accounts.views import LoginView, MeView, RefreshView, RuntimeStatusView
from borrowers.views import (
    AnalystCaseDetailView,
    AnalystCasesView,
    AnalystFieldVerificationRequestView,
    BorrowerAuditLogView,
    BorrowerProfileDetailView,
    BorrowerProfileListCreateView,
    ConsentView,
    DeepScoreView,
    InstantCheckLatestView,
    InstantCheckRunView,
    RequestFieldAgentAssistView,
    ReviewDecisionView,
    SubmitToAnalystView,
    UndoSubmitToAnalystView,
)
from evidence.views import EvidenceDetailView, EvidenceListCreateView, EvidenceProcessView, EvidenceSourceTypeView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/login/", LoginView.as_view()),
    path("api/auth/refresh/", RefreshView.as_view()),
    path("api/auth/me/", MeView.as_view()),
    path("api/runtime-status/", RuntimeStatusView.as_view()),
    path("api/borrower-profiles/", BorrowerProfileListCreateView.as_view()),
    path("api/borrower-profiles/request-field-agent-assist/", RequestFieldAgentAssistView.as_view()),
    path("api/borrower-profiles/<int:pk>/", BorrowerProfileDetailView.as_view()),
    path("api/borrower-profiles/<int:pk>/consent/", ConsentView.as_view()),
    path("api/borrower-profiles/<int:pk>/evidence/", EvidenceListCreateView.as_view()),
    path("api/evidence/<int:pk>/source-type/", EvidenceSourceTypeView.as_view()),
    path("api/evidence/<int:pk>/process/", EvidenceProcessView.as_view()),
    path("api/evidence/<int:pk>/", EvidenceDetailView.as_view()),
    path("api/borrower-profiles/<int:pk>/instant-check/", InstantCheckRunView.as_view()),
    path("api/borrower-profiles/<int:pk>/instant-check/latest/", InstantCheckLatestView.as_view()),
    path("api/borrower-profiles/<int:pk>/submit-to-analyst/", SubmitToAnalystView.as_view()),
    path("api/borrower-profiles/<int:pk>/undo-submit-to-analyst/", UndoSubmitToAnalystView.as_view()),
    path("api/analyst/cases/", AnalystCasesView.as_view()),
    path("api/analyst/cases/<int:pk>/", AnalystCaseDetailView.as_view()),
    path("api/analyst/cases/<int:pk>/deepscore/", DeepScoreView.as_view()),
    path("api/analyst/cases/<int:pk>/request-field-verification/", AnalystFieldVerificationRequestView.as_view()),
    path("api/analyst/reviews/<int:pk>/decision/", ReviewDecisionView.as_view()),
    path("api/borrower-profiles/<int:pk>/audit-logs/", BorrowerAuditLogView.as_view()),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
