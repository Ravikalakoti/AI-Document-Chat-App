from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm

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