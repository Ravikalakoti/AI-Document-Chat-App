from django.shortcuts import redirect
from django.urls import reverse
from accounts.models import Subscription
from docs.models import DocumentQuery

class SubscriptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            print("ppp")
            # Check if user has subscription
            subscription = Subscription.objects.filter(user=request.user).first()
            request.user.is_subscribed = subscription and subscription.is_subscribed
            
            # Check query count for chat endpoint
            if request.path.startswith('/api/chat/'):
                if not request.user.is_subscribed:
                    query_count = DocumentQuery.objects.filter(user=request.user).count()
                    if query_count >= 10:
                        return redirect(reverse('subscription_plan'))
        
        response = self.get_response(request)
        return response