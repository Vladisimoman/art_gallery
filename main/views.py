from django.shortcuts import render, redirect
from .models import Product, Category, Profile
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .forms import SignUpForm, UpdateUserForm, ChangePasswordForm, UserInfoForm

from payment.forms import ShippingForm
from payment.models import ShippingAddress

from django import forms
from django.db.models import Q
import json
from cart.cart import Cart

# Create your views here.
def search(request):
    # determine if they filled out the form
    if request.method == "POST":
        searched = request.POST['searched']
        # Query the products DB Model
        searched = Product.objects.filter(Q(name__icontains=searched) | Q(description__icontains =searched))
        # Test for null
        if not searched:
            messages.success(request, "That product does not exist... please try again")
            return render(request, "search.html", {})
        else:
            return render(request, "search.html", {"searched":searched})
    else:
        return render(request, "search.html", {})


def update_info(request):
    if request.user.is_authenticated:
        # Get current user
        current_user = Profile.objects.get(user__id=request.user.id)
        # Get current user`s shipping info
        shipping_user = ShippingAddress.objects.get(user__id=request.user.id)

        # Get original user form
        form = UserInfoForm(request.POST or None, instance=current_user)
        # Get user`s shipping form
        shipping_form = ShippingForm(request.POST or None, instance=shipping_user)

        if form.is_valid() or shipping_form.is_valid():
            # Save original form
            form.save()
            # Save shipping form
            shipping_form.save()

            messages.success(request, "Your Info Has Been Updated!!")
            return redirect('main')
        return render(request, "update_info.html", {"form":form, "shipping_form":shipping_form})
    else:
        messages.success(request, "You Must Be Logged In To Access That Page!!")
        return redirect('main')

def update_password(request):
    if request.user.is_authenticated:
        current_user = request.user
        # Did they fill out the form
        if request.method == "POST":
            form = ChangePasswordForm(current_user, request.POST)
            # is the form is valid
            if form.is_valid():
                form.save()
                messages.success(request, "Your Password Has Been Updated...")
                login(request, current_user)
                return redirect('update_user')
            else: 
                for error in list(form.errors.values()):
                    messages.error(request, error)
                    return redirect('update_password')
        else:
            form = ChangePasswordForm(current_user)
            return render(request, "update_password.html", {"form":form})

    else:
        messages.success(request, "You Must Be Logged In To Access That Page!!")
        return redirect('main')

def update_user(request):
    if request.user.is_authenticated:
        current_user = User.objects.get(id=request.user.id)
        user_form = UpdateUserForm(request.POST or None, instance=current_user)

        if user_form.is_valid():
            user_form.save()

            login(request, current_user)
            messages.success(request, "User Has Been Updated!!")
            return redirect('main')
        return render(request, "update_user.html", {"user_form":user_form})
    else:
        messages.success(request, "You Must Be Logged In To Access That Page!!")
        return redirect('main')

def category_summary(request):
    categories = Category.objects.all()
    return render(request, 'category_summary.html', {"categories":categories})


def category(request,foo):
    # replace Hyphens with spaces
    foo = foo.replace('-', ' ')
    # Grab the category from url
    try:
        # look up the category
        category = Category.objects.get(name=foo)
        products = Product.objects.filter(category=category)
        return render(request, 'category.html', {'products':products, 'category':category})
    except:
        messages.success(request, ("That category doesn`t exist..."))
        return redirect('main')
    return

def product(request,pk):
    product = Product.objects.get(id=pk)
    return render(request, 'product.html', {'product':product})


def main(request):
    products = Product.objects.all()
    return render(request, 'main.html', {'products':products})

def about(request):
    return render(request, "about.html", {})

def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            # Do some shopping cart stuff
            current_user = Profile.objects.get(user__id=request.user.id)
            # Get their saved cart from db
            saved_cart = current_user.old_cart
            # Convert db string into python dictionary
            if saved_cart:
                # convert to dictionary using Json
                converted_cart = json.loads(saved_cart)
                # Add the load card dictionary to our session
                # Get cart
                cart = Cart(request)
                # Lood throw the cart and add the item from database
                for key, value in converted_cart.items():
                    cart.db_add(product=key, quantity=value)

            messages.success(request, ("You habe been loggin in!"))
            return redirect('main')
        else:
            messages.success(request, ("There was an error... Please try again"))
            return redirect('login')
    else:
        return render(request, 'login.html', {})

def logout_user(request):
    logout(request)
    messages.success(request, ("You have been logged out!"))
    return redirect('main')

def register_user(request):
    form = SignUpForm()
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            # log in user
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, ("Username Createrd - Please Fill Out Your User Info Below!"))
            return redirect('update_info')
        else:
            messages.success(request, ("There was a problem. Try again"))
            return redirect('register')
    else:
        return render(request, 'register.html', {'form':form})