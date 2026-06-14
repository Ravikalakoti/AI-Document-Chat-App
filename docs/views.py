from pathlib import Path
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Document, DocumentChunk, DocumentQuery
from .utils import (
    convert_document_to_html,
    extract_text_from_html,
    extract_text_from_file,
    chunk_text
)

from .vector_store import reset_collection, get_collection
from .embeddings import get_embedding
import ollama
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from django.db.models import Count


# -------------------------
# DASHBOARD
# -------------------------
@login_required
def dashboard(request):
    docs = Document.objects.filter(
        user=request.user
    ).order_by('-created_at')
    return render(request, 'docs/dashboard.html', {'docs': docs})


# -------------------------
# UPLOAD PAGE
# -------------------------
@login_required
def upload_page(request):
    return render(request, 'docs/upload.html')


# -------------------------
# DOCUMENT DETAIL
# -------------------------
@login_required
def document_detail(request, doc_id):
    doc = get_object_or_404(
        Document,
        id=doc_id,
        user=request.user
    )
    chunks = doc.chunks.all().order_by('chunk_index')
    return render(request, 'docs/document_detail.html', {
        'doc': doc,
        'chunks': chunks
    })


# -------------------------
# UPLOAD + INDEXING (FIXED)
# -------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_document(request):
    title = request.data.get('title')
    file = request.FILES.get('file')

    if not title or not file:
        return Response(
            {'error': 'title and file required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    print("UPLOAD:", title, file)

    # Save document
    doc = Document.objects.create(
        user=request.user,
        title=title,
        file=file
    )

    # -------------------------
    # TEXT EXTRACTION (FIXED)
    # -------------------------
    text = extract_text_from_file(doc.file.path)

    print("EXTRACTED TEXT LENGTH:", len(text))

    if not text.strip():
        return Response(
            {'error': 'No text extracted from file'},
            status=400
        )

    doc.extracted_text = text
    doc.save()

    # -------------------------
    # CHUNKING
    # -------------------------
    chunks = chunk_text(text)

    if not chunks:
        return Response(
            {'error': 'No chunks generated'},
            status=400
        )

    # Remove old chunks
    DocumentChunk.objects.filter(document=doc).delete()

    chunk_objs = []
    embeddings = []
    ids = []

    # -------------------------
    # EMBEDDINGS (SAFE FIX)
    # -------------------------
    for i, chunk in enumerate(chunks):
        emb = get_embedding(chunk)

        if not emb:
            print(f"Skipping chunk {i} (embedding failed)")
            continue

        chunk_objs.append(
            DocumentChunk(
                document=doc,
                chunk_index=i,
                text=chunk
            )
        )

        embeddings.append(emb)
        ids.append(f"{doc.id}_{i}")

    # Save chunks in DB
    DocumentChunk.objects.bulk_create(chunk_objs)

    if not embeddings:
        return Response(
            {'error': 'Embedding generation failed'},
            status=500
        )

    # -------------------------
    # VECTOR DB (CHROMA)
    # -------------------------
    collection = reset_collection(doc.id)
    collection.add(
        ids=ids,
        documents=chunks[:len(embeddings)],
        embeddings=embeddings,
        metadatas=[
            {'doc_id': doc.id, 'chunk_index': i}
            for i in range(len(embeddings))
        ]
    )

    return Response({
        'id': doc.id,
        'title': doc.title,
        'chunks': len(embeddings),
        'status': 'uploaded_indexed'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_with_document(request, doc_id):
    doc = get_object_or_404(
        Document,
        id=doc_id,
        user=request.user
    )
    message = request.data.get('message', '').strip()

    DocumentQuery.objects.create(
        user=request.user,
        document=doc,
        question=message
    )

    if not message:
        return Response({'error': 'message required'}, status=400)

    # Query embedding (SAFE)
    query_embedding = get_embedding(message)

    if not query_embedding:
        return Response({'error': 'Query embedding failed'}, status=500)

    collection = get_collection(doc.id)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5,
        include=['documents', 'metadatas']
    )

    contexts = results.get('documents', [[]])[0]
    context_text = "\n\n".join(contexts)

    prompt = f"""
        You are a helpful assistant.
        Answer ONLY from the document context.
        If not present, say "I don't know".

        Context:
        {context_text}

        Question:
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

# -------------------------
# DELETE DOCUMENT
# -------------------------
@login_required
def delete_document(request, id):
    doc = get_object_or_404(
        Document,
        id=id,
        user=request.user
    )

    if request.method == "POST":
        # delete file from storage
        if doc.file:
            doc.file.delete()

        # delete DB record
        doc.delete()

        return redirect('dashboard')

    return redirect('dashboard')

@login_required
def analytics(request):
    user = request.user

    docs_uploaded = Document.objects.filter(user=user).count()

    queries = DocumentQuery.objects.filter(user=user)

    total_queries = queries.count()

    # Most asked questions (global)
    top_questions = (
        queries.values("question")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )

    # queries per document (global)
    per_doc = (
        queries.values("document__title", "document__id")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    return render(request, "docs/analytics.html", {
        "docs_uploaded": docs_uploaded,
        "total_queries": total_queries,
        "top_questions": top_questions,
        "per_doc": per_doc,
        "doc_id": None,  # global view
    })


@login_required
def document_analytics(request, doc_id):
    user = request.user
    doc = get_object_or_404(Document, id=doc_id, user=user)

    queries = DocumentQuery.objects.filter(user=user, document=doc)

    total_queries = queries.count()

    # Most asked questions for this document
    top_questions = (
        queries.values("question")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )

    # You can also add more metrics here if needed

    return render(request, "docs/document_analytics.html", {
        "doc": doc,
        "total_queries": total_queries,
        "top_questions": top_questions,
        "doc_id": doc.id,
    })