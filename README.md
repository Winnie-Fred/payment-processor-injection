1. Create a virtual environment and activate it
2. Install dependencies with pip install -r requirements.txt
3. Create your .env file and enter the following info:
    a. `DJANGO_SECRET_KEY` - Django secret key
    b. `PAYMENT_PROCESSOR` - Payment Processor (Available Options are `payments.paystack.PaystackProcessor` and `payments.credo.CredoProcessor`)
    c. `PAYMENT_PROCESSOR_USE_CALLBACK` - `True` to use callback, `False` to use webhooks for payment notification/processing
    d. `PAYSTACK_SECRET_KEY`
    e. `CREDO_PUBLIC_KEY`
    f. `CREDO_SECRET_KEY`
    g. `CREDO_WEBHOOK_TOKEN`
    h. `CREDO_BUSINESS_CODE`
4. Run python manage.py migrate (no need to makemigrations)
5. Run python manage.py runserver
6. Go to http://127.0.0.1:8000/checkout/
