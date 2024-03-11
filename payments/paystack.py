import hashlib
import hmac
import os
import requests

from django.http.request import HttpRequest
from django.urls import reverse
from django.utils.dateparse import parse_datetime

from requests.exceptions import RequestException

from .interfaces import PaymentProcessor

URL_ROOT = "https://api.paystack.co"
SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')

AUTH_HEADER = f"Bearer {SECRET_KEY}"


class PaystackProcessor(PaymentProcessor):

    name = 'paystack'
    name_readable = 'Paystack'

    def initialize_payment(self, email, amount, reference, callback_url, metadata="{}"):
        initialize_url = f"{URL_ROOT}/transaction/initialize"

        amount *= 100 #  convert amount to kobo value

        try:
            response = requests.post(
                initialize_url,
                json={
                    'email': email,
                    'amount': str(amount),
                    'reference': reference,
                    'callback_url': callback_url,
                    'metadata':metadata,
                },
                headers={
                    'Authorization': AUTH_HEADER
                }
            )

            if response:
                response_dict = response.json()
                if response_dict['status'] == True and 'data' in response_dict:
                    return response_dict['data']['authorization_url']            
                print("response_dict: ", response_dict)
            print("response: ", response.json())
            
        except RequestException as e:
            print(e)
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
                response_dict = response.json()
                if response_dict["status"] == True and response_dict["data"]["status"] == "success":
                    if "paid_at" in response_dict["data"]:
                        payment_date_value = response_dict["data"]["paid_at"]
                        response_dict["data"]["payment_date"] = parse_datetime(payment_date_value)
                    return response_dict
                print("response_dict: ", response_dict)
            print("response: ", response)

        except RequestException as e:
            print(e)
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
        header_signature = request.headers.get('x-paystack-signature')

        payload_hash = hmac.new(SECRET_KEY.encode(
            'utf-8'), payload, hashlib.sha512).hexdigest()

        return hmac.compare_digest(payload_hash, header_signature)
