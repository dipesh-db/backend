from django.urls import path
from .views import *

urlpatterns = [
    path('join/<int:event_id>/', join_event, name='join_event'),
    path('my-events/', get_participated_events, name='get_participated_events'),
]