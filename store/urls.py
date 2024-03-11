from django.urls import path
from . import views


app_name = 'store'

urlpatterns = [
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment_confirmed/<str:reference>/', views.payment_confirmed, name='payment_confirmed'),
    path('payment_gateway_checkout/', views.payment_gateway_checkout, name='payment_gateway_checkout'),
    path('payment_callback/', views.payment_callback, name='payment_callback'),
    path('payment_webhook/', views.payment_webhook, name='payment_webhook'),

]
