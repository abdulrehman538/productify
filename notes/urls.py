from django.urls import path

from . import views

urlpatterns = [
    path('notes/', views.NoteListCreateView.as_view(), name='notes'),
]
