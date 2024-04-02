1. Create a virtual environment and activate it
2. Install dependencies with pip install -r requirements.txt
3. Create your .env file and enter the following info:<br>
   a. `DJANGO_SECRET_KEY` - Django secret key<br>
   b. `PAYMENT_PROCESSOR` - Payment Processor (Available Options are `payments.paystack.PaystackProcessor` and `payments.credo.CredoProcessor`)<br>
   c. `PAYMENT_PROCESSOR_USE_CALLBACK` - `True` to use callback, `False` to use webhooks for payment notification/processing<br>
   d. `PAYSTACK_SECRET_KEY`<br>
   e. `CREDO_PUBLIC_KEY`<br>
   f. `CREDO_SECRET_KEY`<br>
   g. `CREDO_WEBHOOK_TOKEN`<br>
   h. `CREDO_BUSINESS_CODE`<br>
   i. `CREDO_SERVICE_CODE` - Optional, if you want to use dynamic settlement or split payments<br>
5. Run python manage.py migrate (no need to makemigrations)
6. Run python manage.py runserver
7. Go to http://127.0.0.1:8000/checkout/
