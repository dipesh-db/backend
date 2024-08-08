from django.urls import path,include
from . import views

urlpatterns=[
    path('create/',views.create_event,name="Create_events"),
    path('get_events/',views.get_upcoming_events,name="get_events"),
    path('my_events/',views.get_user_created_events,name="upcoming_events"),
    path('delete_event/<int:event_id>/', views.delete_event, name='delete_event'),
    path('edit_event/<int:event_id>/',views.edit_event,name="edit_event")
]