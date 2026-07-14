from django.db import models
from django.contrib.auth.models import User

def user_document_path(instance, filename):
    return f"users/{instance.user.id}/documents/{filename}"

class Document(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="documents"
    )
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to=user_document_path)
    html_path = models.CharField(max_length=500, blank=True, null=True)
    extracted_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class DocumentChunk(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField()
    text = models.TextField()

    def __str__(self):
        return f"{self.document.title} - {self.chunk_index}"



#track user queries
class DocumentQuery(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    question = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    role = models.CharField(max_length=20)  # user / assistant
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)