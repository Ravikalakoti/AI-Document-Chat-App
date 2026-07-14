from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from .models import Subscription

from .forms import SignupForm, ProfileEditForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json


def signup_view(request):

    if request.method == "POST":

        form = SignupForm(request.POST)

        if form.is_valid():

            user = form.save()

            login(request, user)

            return redirect('dashboard')

    else:
        form = SignupForm()

    return render(
        request,
        'signup.html',
        {'form': form}
    )


def login_view(request):

    if request.method == "POST":

        form = AuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():

            user = form.get_user()

            login(request, user)

            return redirect('dashboard')

    else:
        form = AuthenticationForm()

    return render(
        request,
        'login.html',
        {'form': form}
    )


def logout_view(request):

    logout(request)

    return redirect('login')


@login_required
def user_profile_api(request):
    sub = Subscription.objects.get(user=request.user)
    return JsonResponse({
        "username": request.user.username,
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "email": request.user.email,
        "is_subscribed": sub.is_active(),
        "plan": sub.plan_name,
        "subscribed_at": sub.subscribed_at,
        "expires_at": sub.expires_at,
    })


@login_required
@require_POST
def update_profile_api(request):
    try:
        data = json.loads(request.body)
        user = request.user

        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        email = data.get("email", "").strip()

        if not email:
            return JsonResponse({"success": False, "error": "Email is required"}, status=400)

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()

        return JsonResponse({"success": True, "message": "Profile updated successfully"})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)
