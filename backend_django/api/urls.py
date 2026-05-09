from django.urls import path

from .views.auth import register, login_view, logout_view, me
from .views.projects import project_list_create, project_detail, checkpoint_toggle, decision_create, quick_add_parse, grading_prompt_view, smart_defaults_view, activity_library, activity_library_detail
from .views.tools import ai_tool_list_create, ai_tool_update, ai_tool_detail, tool_insights
from .views.dashboard import dashboard_stats
from .views.comments import checkpoint_comments, checkpoint_comment_resolve
from .views.ethics import ethics_start, ethics_node, ethics_evaluate, ethics_scenarios
from .views.templates import template_list, template_detail, document_generate
from .views.assessment import assessment_questions, assessment_submit
from .views.research import submit_consent, start_session, record_response, complete_session
from .views.export import project_export
from .views.verification import scan_file_for_pii, classify_data, bias_audit_view, get_file_columns, redact_pii_in_file, extract_pdf_text, blind_grade_csv
from .views.notifications import notification_list, notification_mark_read, notification_mark_all_read

urlpatterns = [
    # Auth endpoints
    path('auth/register', register, name='register'),
    path('auth/login', login_view, name='login'),
    path('auth/logout', logout_view, name='logout'),
    path('auth/me', me, name='me'),

    # Project endpoints
    path('projects', project_list_create, name='project-list-create'),
    path('projects/quick-add/parse', quick_add_parse, name='project-quick-add-parse'),
    path('projects/<int:project_id>/grading-prompt', grading_prompt_view, name='project-grading-prompt'),
    path('projects/<int:project_id>/smart-defaults', smart_defaults_view, name='project-smart-defaults'),
    path('activities/library', activity_library, name='activity-library'),
    path('activities/library/<int:project_id>', activity_library_detail, name='activity-library-detail'),
    path('projects/<int:project_id>', project_detail, name='project-detail'),
    path('projects/<int:project_id>/checkpoints/<str:checkpoint_id>', checkpoint_toggle, name='checkpoint-toggle'),
    path('projects/<int:project_id>/decisions', decision_create, name='decision-create'),
    path('projects/<int:project_id>/export', project_export, name='project-export'),

    # Dashboard endpoint
    path('dashboard/stats', dashboard_stats, name='dashboard-stats'),

    # AI Tool Registry endpoints
    path('tools', ai_tool_list_create, name='tool-list-create'),
    path('tools/<int:tool_id>', ai_tool_update, name='tool-update'),
    path('tools/<int:tool_id>/detail', ai_tool_detail, name='tool-detail'),
    path('tools/insights', tool_insights, name='tool-insights'),

    # Checkpoint Comment endpoints
    path('projects/<int:project_id>/checkpoints/<str:checkpoint_id>/comments',
         checkpoint_comments, name='checkpoint-comments'),
    path('projects/<int:project_id>/checkpoints/<str:checkpoint_id>/comments/<int:comment_id>/resolve',
         checkpoint_comment_resolve, name='checkpoint-comment-resolve'),

    # Consent endpoints
    path('research/consent', submit_consent, name='submit-consent'),

    # Session tracking endpoints
    path('research/session/start', start_session, name='start-session'),
    path('research/session/response', record_response, name='record-response'),
    path('research/session/complete', complete_session, name='complete-session'),

    # Ethics Assistant endpoints
    path('ethics/start', ethics_start, name='ethics-start'),
    path('ethics/node/<str:node_key>', ethics_node, name='ethics-node'),
    path('ethics/evaluate', ethics_evaluate, name='ethics-evaluate'),
    path('ethics/scenarios', ethics_scenarios, name='ethics-scenarios'),

    # Template/Document endpoints (primary routes)
    path('templates', template_list, name='template-list'),
    path('templates/<str:template_key>', template_detail, name='template-detail'),
    path('documents/generate', document_generate, name='document-generate'),

    # Template/Document aliases (frontend uses these paths)
    path('ethics/templates', template_list, name='template-list-alias'),
    path('ethics/templates/<str:template_key>', template_detail, name='template-detail-alias'),
    path('ethics/generate', document_generate, name='document-generate-alias'),

    # Verification endpoints (automated checkpoint checks)
    path('verify/scan-pii', scan_file_for_pii, name='scan-pii'),
    path('verify/classify-data', classify_data, name='classify-data'),
    path('verify/bias-audit', bias_audit_view, name='bias-audit'),
    path('verify/file-columns', get_file_columns, name='file-columns'),
    path('verify/redact-pii', redact_pii_in_file, name='redact-pii'),
    path('verify/extract-pdf', extract_pdf_text, name='extract-pdf'),
    path('verify/blind-grade-csv', blind_grade_csv, name='blind-grade-csv'),

    # Assessment endpoints
    path('assessment/questions', assessment_questions, name='assessment-questions'),
    path('assessment/submit', assessment_submit, name='assessment-submit'),

    # Notification endpoints
    path('notifications', notification_list, name='notification-list'),
    path('notifications/read-all', notification_mark_all_read, name='notification-mark-all-read'),
    path('notifications/<int:notification_id>/read', notification_mark_read, name='notification-mark-read'),
]
