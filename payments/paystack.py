import hashlib
import hmac
import os
import requests
import json

from django.http.request import HttpRequest
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from django.conf import settings


from requests.exceptions import RequestException

from .interfaces import PaymentProcessor

from store.utils import OnlineTransactionStatus


URL_ROOT = "https://api.paystack.co"
SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')

AUTH_HEADER = f"Bearer {SECRET_KEY}"


class PaystackProcessor(PaymentProcessor):

    name = 'paystack'
    name_readable = 'Paystack'

    def initialize_payment(self, email, amount, reference, callback_url="", metadata="{}"):
        initialize_url = f"{URL_ROOT}/transaction/initialize"

        amount *= 100 #  convert amount to kobo value

        body = {
            'email': email,
            'amount': str(amount),
            'reference': reference,
            'metadata':metadata,
        }
        
        if settings.PAYMENT_PROCESSOR_USE_CALLBACK:
            body['callback_url'] = callback_url

        try:
            response = requests.post(
                initialize_url,
                json=body,
                headers={
                    'Authorization': AUTH_HEADER
                }
            )

            if response:
                try:
                    response_dict = response.json()
                except json.JSONDecodeError:
                    return ''
        
                if response_dict['status'] == True and 'data' in response_dict:
                    return response_dict['data']['authorization_url']            
                print("response_dict: ", response_dict)
            print("response: ", response.json())
            
        except RequestException as e:
            print("An error occured while making the request: ", e)
        except Exception as e:
            print("An error occured: ", e)
        return ''

    def verify_payment(self, reference):

        url = f"{URL_ROOT}/transaction/verify/{reference}"

        try:
            response = requests.get(
                url,
                headers={
                    'Authorization': AUTH_HEADER
                }
            )

            if response:
                try:
                    response_dict = response.json()
                except json.JSONDecodeError:
                    return {}
                
                print(response_dict)

                if response_dict["status"] == True and 'data' in response_dict:
                    if response_dict["data"]["status"] == "success":
                        response_dict["data"]["status"] = OnlineTransactionStatus.SUCCESSFUL
                    else:
                        response_dict["data"]["status"] = OnlineTransactionStatus.FAILED
                    if "paid_at" in response_dict["data"]:
                        payment_date_value = response_dict["data"]["paid_at"]
                        response_dict["data"]["payment_date"] = parse_datetime(payment_date_value)
                    return response_dict
                print("response_dict: ", response_dict)
            print("response: ", response)

        except RequestException as e:
            print("An error occured while making the request: ", e)
        except Exception as e:
            print("An error occured: ", e)
        return {}


    def verify_event(self, request: HttpRequest):
        '''
        Verify that an event is from Paystack using the header [X-Paystack-Signature]
        in the request header which is a [HMAC SHA512] signature of the request payload
        signed using the SECRET_KEY

        This will create a hash using the secret key and the request body and the running
        a comparison between the header and the one created here. 

        Returns true if they are same.
        '''

        payload = request.body
        header_signature = request.headers.get('x-paystack-signature', '')

        payload_hash = hmac.new(SECRET_KEY.encode(
            'utf-8'), payload, hashlib.sha512).hexdigest()

        return hmac.compare_digest(payload_hash, header_signature)
    
    def format_payload_webhook(self, payload):
        '''
        Formats payload to universal format followed by all integrated payment gateways to 
        avoid key errors. Paystack payload structure is mostly used to model/format 
        other payment gateway payloads.
        '''
        if payload["event"].lower() == "charge.success":
            payload["event"] = OnlineTransactionStatus.SUCCESSFUL
        if "paid_at" in payload["data"]:
            payment_date_value = payload["data"]["paid_at"]
            payload["data"]["payment_date"] = parse_datetime(payment_date_value)
        return payload
