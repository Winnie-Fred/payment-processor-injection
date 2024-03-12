import os
import importlib

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings


# Create your models here.

class PaymentProcessorMixin:
    name = None
    name_readable = None

def get_supported_payment_processors():
    processors = {}
    payments_dir = os.path.join(settings.BASE_DIR, 'payments')

    for filename in os.listdir(payments_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = f"payments.{filename[:-3]}"
            module = importlib.import_module(module_name)
            for obj in module.__dict__.values():
                if isinstance(obj, type) and issubclass(obj, PaymentProcessorMixin):
                    if obj.name is not None:
                        processors[obj.name] = obj.name_readable

    return processors

supported_payment_processors = get_supported_payment_processors()


class PaymentStatus(models.TextChoices):
    UNPROCESSED = 'UP', _('Unprocessed')
    COMPLETED = 'CM', _('Completed')
    FAILED  = 'FD', _('Failed')


class Payment(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    amount = models.FloatField()
    reference = models.CharField(max_length=64, unique=True, blank=True)
    date = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=2, choices=PaymentStatus.choices, default=PaymentStatus.UNPROCESSED)
    processor = models.CharField(max_length=20, choices=[(processor_name, processor_name_readable) for processor_name, processor_name_readable in supported_payment_processors.items()], default='')

    def __str__(self) -> str:
        return f"{self.user} [Ref-{self.reference}] payment"  
