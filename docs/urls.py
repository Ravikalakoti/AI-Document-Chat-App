from django.urls import path
from .views import dashboard, upload_page, document_detail, upload_document, chat_with_document

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('upload/', upload_page, name='upload_page'),
    path('doc/<int:doc_id>/', document_detail, name='document_detail'),
    path('api/upload/', upload_document, name='upload_document'),
    path('api/chat/<int:doc_id>/', chat_with_document, name='chat_with_document'),
]