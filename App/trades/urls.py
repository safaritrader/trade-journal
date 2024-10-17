from django.urls import path
from . import views

urlpatterns = [
    path('', views.journal_list, name='journal_list'),
    path('performance/', views.performance_analysis, name='performance_analysis'),
    path('journal-detail/<int:entry_id>/', views.journal_detail, name='journal_detail'),
    path('journal-update/<int:entry_id>/', views.update_journal, name='update_journal'),  # Add this line
]

