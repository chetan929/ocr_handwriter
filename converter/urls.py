from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),                    # OCR page
    path('handwriting/', views.handwriting, name='handwriting'),  # handwriting generation page
]
