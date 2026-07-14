from pathlib import Path
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from .models import Document, DocumentChunk, DocumentQuery, ChatMessage
from accounts.models import Subscription
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

def home(request):
    if request.user.is_authenticated:
        # If authenticated, redirect to dashboard
        return redirect('dashboard')
    
    # Free tier info
    free_limit = 10
    free_features = [
        "Up to 10 queries",
        "Upload up to 5 documents",
        "Basic analytics",
        "Standard support"
    ]
    
    # Premium tier info
    premium_price = "₹499/month"
    premium_features = [
        "Unlimited queries",
        "Unlimited document upload",
        "Advanced analytics",
        "Priority support",
        "AI-powered insights"
    ]
    
    return render(request, 'docs/home.html', {
        'free_limit': free_limit,
        'free_features': free_features,
        'premium_price': premium_price,
        'premium_features': premium_features,
    })

# -------------------------
# DASHBOARD
# -------------------------
@login_required
def dashboard(request):
    user = request.user
    
    docs = Document.objects.filter(user=user)
    query_count = DocumentQuery.objects.filter(user=user).count()
    
    subscription = Subscription.objects.filter(user=user).first()
    is_subscribed = subscription and subscription.is_subscribed
    
    return render(request, 'docs/dashboard.html', {
        'docs': docs,
        'query_count': query_count,
        'is_subscribed': is_subscribed,
    })


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

    messages = ChatMessage.objects.filter(
        user=request.user,
        document=doc
    ).order_by("created_at")

    return render(request, 'docs/document_detail.html', {
        'doc': doc,
        'chunks': chunks,
        'messages': messages
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
    user = request.user
    name = user.first_name if user.first_name else user.username

    try:
        # Check subscription
        subscription = Subscription.objects.filter(user=user).first()
        is_subscribed = subscription and subscription.is_subscribed

        if not is_subscribed:
            query_count = DocumentQuery.objects.filter(user=user).count()

            if query_count >= 10:
                return Response({
                    'error': 'limit_exceeded',
                    'message': 'You have reached your 10 query limit. Subscribe for unlimited access.',
                    'query_count': query_count,
                    'limit': 10
                }, status=403)


        doc = get_object_or_404(
            Document,
            id=doc_id,
            user=user
        )

        message = request.data.get('message', '').strip()

        if not message:
            return Response({
                'error': 'message required'
            }, status=400)


        # Save user message
        ChatMessage.objects.create(
            user=user,
            document=doc,
            role="user",
            message=message
        )


        # -------- RAG SEARCH --------

        query_embedding = get_embedding(message)

        if not query_embedding:
            return Response({
                'error': 'Query embedding failed'
            }, status=500)


        collection = get_collection(doc.id)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5,
            include=['documents', 'metadatas']
        )


        contexts = results.get('documents', [[]])[0]

        context_text = "\n\n".join(contexts)


        # -------- PREVIOUS CHAT MEMORY --------

        history = ChatMessage.objects.filter(
            user=user,
            document=doc
        ).order_by("-created_at")[:10]


        messages = []


        for chat in reversed(history):
            messages.append({
                "role": chat.role,
                "content": chat.message
            })


        # Current AI instruction

        prompt = f"""
            You are a helpful AI assistant.

            User name:
            {name}

            Rules:
            - Use user's name occasionally.
            - Be conversational.
            - Answer only from document context.
            - Do not invent information.
            - If answer is not available say:

            "I'm sorry, I couldn't find that information in the uploaded document.

            If you have any questions or need further assistance, please contact Ravi.

            📧 Email: ravikalakoti16@gmail.com"


            Document Context:

            {context_text}


            Current Question:

            {message}
        """


        messages.append({
            "role": "user",
            "content": prompt
        })


        # -------- OLLAMA --------

        from ollama import Client

        client = Client(
            host='http://localhost:11434'
        )


        response = client.chat(
            model='llama3.1',
            messages=messages
        )


        reply_content = response['message']['content']


        # Save AI response

        ChatMessage.objects.create(
            user=user,
            document=doc,
            role="assistant",
            message=reply_content
        )


        # Existing query tracking

        DocumentQuery.objects.create(
            user=user,
            document=doc,
            question=message
        )


        query_count = DocumentQuery.objects.filter(
            user=user
        ).count()


        return Response({
            'reply': reply_content,
            'matched_chunks': len(contexts),
            'query_count': query_count,
            'limit': 10,
            'is_subscribed': is_subscribed
        })


    except Exception as e:
        print(
            "chat_with_document error:",
            e
        )

        return Response({
            'error': 'Internal server error'
        }, status=500)


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

@login_required
def subscription_plan(request):
    user = request.user
    query_count = DocumentQuery.objects.filter(user=user).count()
    
    subscription = Subscription.objects.filter(user=user).first()
    is_subscribed = subscription and subscription.is_subscribed
    
    return render(request, 'docs/subscription_plan.html', {
        'query_count': query_count,
        'is_subscribed': is_subscribed,
    })

@login_required
def subscribe(request):
    user = request.user
    
    # Create or update subscription (DUMMY - no payment)
    subscription = Subscription.objects.filter(user=user).first()
    if not subscription:
        subscription = Subscription(user=user)
    
    subscription.is_subscribed = True
    subscription.subscribed_at = timezone.now()
    subscription.expires_at = timezone.now() + timedelta(days=30)
    subscription.plan_name = "Premium"
    subscription.save()
    
    return redirect('dashboard')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_history(request, doc_id):

    document = get_object_or_404(
        Document,
        id=doc_id,
        user=request.user
    )

    messages = ChatMessage.objects.filter(
        document=document,
        user=request.user
    ).order_by("created_at")

    return Response([
        {
            "role": msg.role,
            "message": msg.message
        }
        for msg in messages
    ])