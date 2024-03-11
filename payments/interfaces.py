from django.http.request import HttpRequest
from .models import PaymentProcessorMixin


class PaymentProcessor(PaymentProcessorMixin):
    def initialize_payment(self, email, amount, reference, callback_url, metadata="{}"):
        """
        Initialize a payment transaction.

        This method initiates a payment transaction for the specified email, amount, and reference by sending a request to the payment provider's API's transaction initialize endpoint.

        Parameters:
            email (str): The email address of the customer making the payment.
            amount (float): The amount to be charged for the payment transaction.
            reference (str): A unique identifier or reference for this payment transaction.
            callback_url (str): A string containing the url to redirect the user to after payment attempt
            metadata (str, optional): A JSON-formatted string containing additional information or custom data to be associated with the payment. Defaults to an empty JSON string.

        Returns:
            str: The URL to the payment provider's authorization page. If the request to the payment provider's API fails, an empty string is returned.
                
        Example:
            >>> initialize_payment("customer@example.com", 99.99, "ORDER123")
            "https://paymentprovider.com/authorize/TXN987654321"

        Note:
            The `amount` is converted to kobo (a subunit of the currency) to match the payment provider's requirements.
            If the request to the payment provider's API's transaction initialize endpoint is successful, the method returns the authorization URL where the user can complete the payment process.
            If the request fails, an empty string is returned.
            The `metadata` parameter allows you to include any additional information relevant to the payment, which will be associated with the transaction in the payment provider's records.
        """
        pass



    def verify_payment(self, reference):
        """
        Verify the status of a payment transaction.

        This method checks the status of a payment transaction based on the provided reference by sending a request to the payment provider's API's transaction verify endpoint`.

        Parameters:
            reference (str): A unique identifier or reference for the payment transaction.

        Returns:
            dict or {}: If the payment verification is successful and the transaction status is "success", a dictionary containing the payment verification details is returned. Otherwise, if the verification fails or the payment status is not "success", an empty dictionary is returned.

        Example:
            >>> verify_payment("ORDER123")
            {
                "status": "success",
                "reference": "ORDER123",
                "amount": 99.99,
                "transaction_date": "2023-07-25 12:34:56",
                # Additional verification details from the payment provider
            }

        Note:
            The `reference` parameter is used to identify the specific payment transaction to be verified.
            The method sends a request to the payment provider's API's transaction verify endpoint with the given reference and retrieves the payment verification details.
            If the payment status is "success", the method returns the response dictionary containing the verification details.
            If the verification fails, an empty dictionary is returned.
        """
        pass


    def verify_event(self, request: HttpRequest):
        """
        Verify the authenticity of a payment gateway event, that the event is indeed from the payment gateway using the header.

        This method checks the authenticity of a payment gateway event by comparing the request payload hash with the signature provided in the request header.

        Parameters:
            request (HttpRequest): The HTTP request object containing the payment gateway event payload and the signature in the header.

        Returns:
            bool: True if the event is verified and authentic, False otherwise.


        Note:
            The `request` parameter should be a Django `HttpRequest` object.
            The method retrieves the event payload from the request body and the signature from the appropriate header, based on the payment gateway's specifications.
            It then calculates the payload hash using HMAC-SHA512 (or the appropriate hashing algorithm) with the provided secret key or authentication token.
            If the calculated payload hash matches the header signature in a secure manner (constant-time comparison), the method returns True, indicating the event's authenticity.
            If the comparison fails or there is an issue with the request or the provided authentication mechanism, the method returns False, indicating the event is not authentic or cannot be verified.
        """
        pass

    
