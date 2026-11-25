from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('a-propos/', views.AboutView, name='a_propos'),
    path('contact/', views.ContactView, name='contact'),
    path('administration/messages/', views.liste_messages_contact,         name='liste_messages_contact'),
    path('administration/messages/<int:message_id>/etat/',         views.marquer_message_contact, name='marquer_message_contact'),
    path('administration/messages/<int:message_id>/supprimer/',         views.supprimer_message_contact, name='supprimer_message_contact'),
    path('administration/messages/<int:message_id>/repondre/', views.repondre_message_contact, name='repondre_message_contact'),
]
