import hashlib
import os
import hashlib
import json
import requests

from datetime import datetime

from django.http.request import HttpRequest
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.conf import settings

from requests.exceptions import RequestException

from .interfaces import PaymentProcessor
from store.utils import OnlineTransactionStatus



PUBLIC_KEY = os.getenv('CREDO_PUBLIC_KEY')
SECRET_KEY = os.getenv('CREDO_SECRET_KEY')
CREDO_SERVICE_CODE = os.getenv('CREDO_SERVICE_CODE')

CREDO_LIVE_URL="https://api.credocentral.com"
CREDO_DEMO_URL="https://api.public.credodemo.com"


URL_ROOT = CREDO_LIVE_URL if settings.LIVE else CREDO_DEMO_URL


class CredoProcessor(PaymentProcessor):

    name = 'credo'
    name_readable = 'Credo'

    def initialize_payment(self, email, amount, reference, callback_url="", metadata="{}"):
        initialize_url = f"{URL_ROOT}/transaction/initialize"

        amount *= 100 #  convert amount to kobo value  

        body= {
                'email': email,
                'amount': str(int(amount)),
                'reference': reference,
                'metadata':metadata,
        }
        
        if settings.PAYMENT_PROCESSOR_USE_CALLBACK:
            body['callbackUrl'] = callback_url

        if CREDO_SERVICE_CODE:
            body['serviceCode'] = CREDO_SERVICE_CODE #  for split payments or dynamic settlement


        try:
            response = requests.post(
                initialize_url,
                json=body,
                headers={
                    'Authorization': PUBLIC_KEY,                    
                }
            )
            if response:

                try:
                    response_dict = response.json()
                except json.JSONDecodeError:
                    return ''
                
                if response_dict['status'] == 200 and 'data' in response_dict:
                    return response_dict['data']['authorizationUrl']
                print("response_dict: ", response_dict)
            print("response: ", response.content)

        except RequestException as e:
            print("An error occured while making the request: ", e)
        except Exception as e:
            print("An error occured: ", e)
        return ''


    def verify_payment(self, reference):

        url = f"{URL_ROOT}/transaction/{reference}/verify"

        try:
            response = requests.get(
                url,
                headers={
                    'Authorization': SECRET_KEY,                    
                }
            )

            if response:
                try:
                    response_dict = response.json()
                except json.JSONDecodeError:
                    return {}
                
                if response_dict["status"] == 200 and 'data' in response_dict:
                    if response_dict["data"]["status"] == 0:
                        response_dict["data"]["status"] = OnlineTransactionStatus.SUCCESSFUL
                    else:
                        response_dict["data"]["status"] = OnlineTransactionStatus.FAILED
                    if "transactionDate" in response_dict["data"]:
                        payment_date_value = response_dict["data"]["transactionDate"] 
                        date = timezone.make_aware(parse_datetime(payment_date_value), timezone=timezone.get_current_timezone())                       
                        response_dict["data"]["payment_date"] = date
                    return response_dict
                print("response_dict: ", response_dict)
            print("response: ", response.content)

        except RequestException as e:
            print("An error occured while making the request: ", e)
        except Exception as e:
            print("An error occured: ", e)
        return {}


    def verify_event(self, request: HttpRequest):
        '''
        Verify that an event is from Credo using the header [X-Credo-Signature]
        in the request header which is a [HMAC SHA512] signature of the 
        combination of the webhook token and the business code.

        This will compare the result to the header signature. 

        Returns true if they are same.
        '''
        
        header_signature = request.headers.get('X-Credo-Signature', '')
        token = os.getenv('CREDO_WEBHOOK_TOKEN')
        business_code = os.getenv('CREDO_BUSINESS_CODE')
        signed_content = f"{token}{business_code}"
        sha512_hash = hashlib.sha512(signed_content.encode()).hexdigest()        
        return sha512_hash == header_signature


    def format_payload_webhook(self, payload):
        '''
        Format payload to look like other payment processor payloads 
        to avoid key error. Modelled to look like Paystack's payload.
        '''

        
        if payload["event"].lower() == "transaction.successful":
            payload["event"] = OnlineTransactionStatus.SUCCESSFUL
        elif payload["event"].lower() == "transaction.failed":
            payload["event"] = OnlineTransactionStatus.FAILED
        if "transactionDate" in payload["data"]: #  convert timestamp to timezone aware python datetime
            payment_date_value = payload["data"]["transactionDate"] 
            timestamp = payment_date_value / 1000
            transaction_datetime = datetime.utcfromtimestamp(timestamp)
            transaction_datetime_utc = timezone.make_aware(transaction_datetime, timezone.utc) 
            date = transaction_datetime_utc.astimezone(timezone.get_current_timezone())
            payload["data"]["payment_date"] = date
        if "businessRef" in payload["data"]:
            payload["data"]["reference"] = payload["data"]["businessRef"]
        return payload
        

