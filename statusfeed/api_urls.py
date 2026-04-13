from django.urls import path

from . import views

app_name = 'statusfeed_api'

urlpatterns = [
    path('', views.list_statuses, name='list_statuses'),
    path('me/', views.my_statuses, name='my_statuses'),
    path('create/', views.create_status, name='create_status'),
    path('<int:status_id>/', views.status_detail, name='status_detail'),
]
