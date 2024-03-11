import json
import logging

from django.shortcuts import render, redirect
from payments.factory import get_payment_processor
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login

from payments.models import Payment, PaymentStatus
from payments.utils import generate_unique_reference

from .forms import CustomSignupForm

payment_processor = get_payment_processor()

logger = logging.getLogger(__name__)


def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('store:checkout')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def signup(request):
    if request.method == 'POST':
        form = CustomSignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('store:login')
    else:
        form = CustomSignupForm()
    return render(request, 'signup.html', {'form': form})

def checkout(request):
    # This view should have the button the user clicks to make payment
    # It could also contain form processing if you collect any additional info from them
    # If form is valid, render to the payment_gateway_checkout url
    return render(request, 'checkout.html')

def payment_confirmed(request, reference):
    return render(request, 'payment_confirmed.html', context={'reference':reference})

# Create your views here.
@login_required(login_url='store:login')
def payment_gateway_checkout(request):
    if request.method == "POST":

        amount = 400 # Use the school fees amount here

        # Initialize unprocessed payment to get reference for tracking payment
        payment_processor = get_payment_processor()
        payment = Payment(
            user=request.user,
            amount=amount,
            processor=payment_processor.name
        )
        payment.reference = generate_unique_reference(
            payment, char_length=8)
        payment.save()

        callback_url = request.build_absolute_uri(reverse("store:payment_callback"))
        payment_url = payment_processor.initialize_payment(
            request.user.email, amount, payment.reference, callback_url)
        if payment_url:
            return redirect(payment_url)
        else:
            messages.error(request, "Cannot process payment at the moment.")
    return redirect('store:checkout')



def payment_callback(request):
    '''
    Callback from the payment gateway page.

    Expected in request.GET dict - reference
    '''

    reference = request.GET.get("reference")
    payload = payment_processor.verify_payment(reference)

    if payload:
        try:
            payment = Payment.objects.get(reference=reference)
            if payment.status == PaymentStatus.UNPROCESSED:
                logger.info("Processing payment via callback")
                print("Processing payment via callback")
                _post_payment_action(payment, payload)
                messages.success(request, "Payment processed successfully.")
            else:
                logger.info("payment_callback - payment already completed")
                messages.success(request, "Payment processed successfully.")

            # redirect to order confirmed
            return redirect('store:payment_confirmed', reference=payment.reference)

        except Payment.DoesNotExist:
            logger.error(
                "payment_callback - payment does not exist")
            messages.error(request, "Payment does not exist.")
    else:
        messages.error(request, "Unable to verify payment.")

    return redirect('store:checkout')


def _post_payment_action(payment, payload):
    paid_at = payload["data"]["payment_date"]

    with transaction.atomic():

        # get and update payment object
        payment.date  = paid_at
        payment.status = PaymentStatus.COMPLETED
        payment.save()

        # perform any other actions here that should happen after successful transaction
                    
    # You can send transaction successful email via signals or so


@csrf_exempt
@require_POST
def payment_webhook(request):
    
    if not payment_processor.verify_event(request):
        logger.warning("Event verification failed")
        return HttpResponse('Event verification failed', status=400)

    payload = json.loads(request.body)

    # Handle [charge.success] event
    if payload["event"] == "charge.success":
        reference = payload["data"]["reference"]
        try:
            payment = Payment.objects.get(reference=reference)

            if payment.status == PaymentStatus.UNPROCESSED:
                logger.info("Processing payment via webhook")
                print("Processing payment via webhook")
                _post_payment_action(payment, payload)

            logger.info("payment_webhook [charge.success] - payment already completed")
        except Payment.DoesNotExist:
            logger.error("payment_webhook [charge.success] - payment does not exist")
            return HttpResponse('Payment does not exist', status=404)
    
    return HttpResponse('Webhook processed successfully', status=200)