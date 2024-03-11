from typing import Type
from django.db.models import Model
from django.http.response import JsonResponse
from django.utils.crypto import get_random_string


def generate_unique_reference(instance: Type[Model], new_ref=None, char_length=64) -> str:
    ''' 
    Generates a unique reference code of 64 [default] characters 
    for the reference field of an instance Model.

    Note: The model MUST have a field [reference]
    '''
    if new_ref:
        ref = new_ref
    else:
        ref = get_random_string(char_length)

    instance_class = instance.__class__
    qs = instance_class.objects.filter(reference=ref)

    if qs.exists():
        new_ref = get_random_string(char_length)
        return generate_unique_reference(instance, new_ref=new_ref)

    return ref
