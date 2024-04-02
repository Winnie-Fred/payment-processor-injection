import json
import logging

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login, authenticate

from payments.factory import get_payment_processor
from payments.models import Payment, PaymentStatus
from payments.utils import generate_unique_reference

from store.utils import MessageTypes, OnlineTransactionStatus

from .forms import CustomSignupForm

payment_processor = get_payment_processor()

logger = logging.getLogger(__name__)


def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
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

    if request.method == 'GET' and 'reference' in request.GET:
        reference = request.GET.get("reference")
        payload = payment_processor.verify_payment(reference)

        if payload:
            try:
                payment = Payment.objects.get(reference=reference)
                if payment.status == PaymentStatus.UNPROCESSED:
                    logger.info("Processing payment via callback")
                    print("Processing payment via callback")    
                    if payload["data"]["status"] == OnlineTransactionStatus.SUCCESSFUL:
                        result = _post_successful_payment_actions(payment, payload["data"]["payment_date"], request)
                        if result['status'] == MessageTypes.SUCCESS.value:
                            messages.success(request, result['message'])
                            return redirect('store:payment_confirmed', reference=payment.reference)
                        else:
                            message = "Payment was successful but something went wrong."
                            messages.error(request, message)
                            logger.info(message)
                            print(message)   
                            return render(request, "payment-processing-result.html", result)
                    elif payload["data"]["status"] == OnlineTransactionStatus.FAILED:
                        message = "Payment was unsuccessful."
                        messages.error(request, message)
                        logger.info(message)
                        print(message)   
                        result = _post_failed_payment_actions(payment, payload["data"]["payment_date"], request)
                        return render(request, "payment-processing-result.html", result)
                else:
                    logger.info("payment_callback - payment already processed")
                    print("payment_callback - payment already processed")
                    messages.info(request, "That payment has already been processed")

            except Payment.DoesNotExist:
                logger.error("payment_callback - payment does not exist")
                messages.error(request, "Payment does not exist.")
        else:
            logger.error("Unable to verify payment.")
            messages.error(request, "Unable to verify payment.")

    return redirect('store:checkout')


def _post_successful_payment_actions(payment, date, request):

    try:
        with transaction.atomic():

            # get and update payment object
            payment.date  = date
            payment.status = PaymentStatus.COMPLETED
            payment.save()

            # perform any other actions here that should happen after successful transaction
            return {'status':MessageTypes.SUCCESS.value, 'message': 'Payment processed successfully', 'payment': payment}
               
        # You can send transaction successful email here

    except Exception:
        return {'status': MessageTypes.ERROR.value, 'message': 'Oops. An error occurred. Please report the issue to the developers.', 'payment': payment}    

def _post_failed_payment_actions(payment, date, request):
    
    try:  
        with transaction.atomic():  
            payment.date = date                      
            payment.status = PaymentStatus.FAILED
            payment.save()
            return {'status': MessageTypes.ERROR.value, 'message': 'Oops. Payment was unsuccessful.', 'payment':payment}
    except Exception:
        return {'status': MessageTypes.ERROR.value, 'message': 'Oops. An error occurred. Please report the issue to the developers.', 'payment':payment}    

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