from pathlib import Path
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Document, DocumentChunk
from .utils import convert_document_to_html, extract_text_from_html, chunk_text
from .vector_store import reset_collection, get_collection
from .embeddings import get_embedding
import ollama

def dashboard(request):
    docs = Document.objects.order_by('-created_at')
    return render(request, 'docs/dashboard.html', {'docs': docs})

def upload_page(request):
    return render(request, 'docs/upload.html')

def document_detail(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    chunks = doc.chunks.all().order_by('chunk_index')
    return render(request, 'docs/document_detail.html', {'doc': doc, 'chunks': chunks})

@api_view(['POST'])
def upload_document(request):
    title = request.data.get('title')
    file = request.FILES.get('file')

    if not title or not file:
        return Response({'error': 'title and file required'}, status=status.HTTP_400_BAD_REQUEST)

    doc = Document.objects.create(title=title, file=file)

    ext = Path(doc.file.path).suffix.lower()
    html_path = None

    if ext in ['.doc', '.docx', '.odt', '.odf']:
        html_path = convert_document_to_html(doc.file.path)
        if html_path.exists():
            doc.html_path = str(html_path.relative_to(settings.BASE_DIR))

    text = ''
    if html_path and html_path.exists():
        text = extract_text_from_html(html_path)

    doc.extracted_text = text
    doc.save()

    chunks = chunk_text(text)

    DocumentChunk.objects.filter(document=doc).delete()
    chunk_objs = []
    embeddings = []
    ids = []

    for i, chunk in enumerate(chunks):
        chunk_objs.append(DocumentChunk(document=doc, chunk_index=i, text=chunk))
        embeddings.append(get_embedding(chunk))
        ids.append(f'{doc.id}_{i}')

    DocumentChunk.objects.bulk_create(chunk_objs)

    collection = reset_collection(doc.id)
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=[{'doc_id': doc.id, 'chunk_index': i} for i in range(len(chunks))]
    )

    return Response({'id': doc.id, 'title': doc.title, 'chunks': len(chunks), 'status': 'uploaded_indexed'})

@api_view(['POST'])
def chat_with_document(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    message = request.data.get('message', '').strip()

    if not message:
        return Response({'error': 'message required'}, status=400)

    query_embedding = get_embedding(message)
    collection = get_collection(doc.id)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5,
        include=['documents', 'metadatas']
    )

    contexts = results['documents'][0] if results.get('documents') else []
    context_text = "\n\n".join(contexts)

    prompt = f"""
You are a helpful assistant. Answer only from the document context.
If the answer is not present, say you don't know.

Document context:
{context_text}

User question:
{message}
"""

    response = ollama.chat(
        model='llama3.1',
        messages=[{'role': 'user', 'content': prompt}]
    )

    return Response({
        'reply': response['message']['content'],
        'matched_chunks': len(contexts)
    })