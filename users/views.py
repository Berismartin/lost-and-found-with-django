from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
from .models import User, UserProfile
from .forms import UserRegistrationForm, UserProfileForm, UserUpdateForm


def register_user(request):
    """View to handle user registration"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    # Create UserProfile automatically
                    UserProfile.objects.create(user=user)
                    
                    # Log in the user
                    username = form.cleaned_data.get('username')
                    password = form.cleaned_data.get('password1')
                    user = authenticate(username=username, password=password)
                    
                    if user:
                        login(request, user)
                        messages.success(request, f'Welcome {user.first_name}! Your account has been created successfully.')
                        return redirect('profile_view')
                    
            except Exception as e:
                messages.error(request, 'An error occurred during registration. Please try again.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/registration.html', {'form': form})


def login_user(request):
    """View to authenticate and log in users"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            
            # Redirect to next page if specified, otherwise to home
            next_page = request.GET.get('next', '/')
            return redirect(next_page)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'users/login.html')


def logout_user(request):
    """View to log out the user"""
    user_name = request.user.first_name if request.user.is_authenticated else ''
    logout(request)
    if user_name:
        messages.success(request, f'Goodbye, {user_name}! You have been logged out successfully.')
    return redirect('login_user')


@login_required
def profile_view(request):
    """View to display the user's profile"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist
        profile = UserProfile.objects.create(user=request.user)
    
    # Get item counts for the user
    lost_count = request.user.items.filter(status='lost').count()
    found_count = request.user.items.filter(status='found').count()
    claimed_count = request.user.items.filter(status='claimed').count()
    
    return render(request, 'users/profile.html', {
        'user': request.user,
        'profile': profile,
        'lost_count': lost_count,
        'found_count': found_count,
        'claimed_count': claimed_count,
    })


@login_required
def edit_profile(request):
    """View to handle form submission for updating the UserProfile"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile_view')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)
    
    return render(request, 'users/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })
