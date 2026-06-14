from django.urls import path
from .views import dashboard, upload_page, document_detail, upload_document, chat_with_document,\
    delete_document, analytics, document_analytics, home, subscription_plan, subscribe

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
    path('upload/', upload_page, name='upload_page'),
    path('doc/<int:doc_id>/', document_detail, name='document_detail'),
    path('api/upload/', upload_document, name='upload_document'),
    path('api/chat/<int:doc_id>/', chat_with_document, name='chat_with_document'),
    path('delete/<int:id>/', delete_document, name='delete_document'),
    path('analytics/', analytics, name='analytics'),
    path("analytics/doc/<int:doc_id>/", document_analytics, name="document_analytics"),
    path('', home, name='home'),
    path('subscription/', subscription_plan, name='subscription_plan'),
    path('subscribe/', subscribe, name='subscribe'),
]