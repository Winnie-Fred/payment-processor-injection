from django.conf import settings
from importlib import import_module

def get_payment_processor():
    processor_path = settings.PAYMENT_PROCESSOR
    module_path, class_name = processor_path.rsplit('.', 1)
    module = import_module(module_path)
    PaymentProcessor = getattr(module, class_name)
    return PaymentProcessor()