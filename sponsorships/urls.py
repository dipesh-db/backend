from django.urls import path
from .views import *

urlpatterns = [
    path('<int:event_id>/', sponsor_event, name='sponsor_event'),
    path('get_sponsored_events/',get_user_sponsored_events,name='user_sponsored_events'),
]
