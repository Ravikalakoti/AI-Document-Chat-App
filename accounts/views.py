from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from .models import Subscription

from .forms import SignupForm


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

def user_profile_api(request):
    sub = Subscription.objects.get(user=request.user)

    return JsonResponse({
        "username": request.user.username,
        "is_subscribed": sub.is_active(),
        "plan": sub.plan_name,
        "subscribed_at": sub.subscribed_at,
        "expires_at": sub.expires_at,
    })