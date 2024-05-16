from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('edit/<str:pos>/', views.edit_plate, name='edit_plate'),
    path('load/', views.load_csv, name='load_csv'),
    path('save/', views.save_csv, name='save_csv'),
]
