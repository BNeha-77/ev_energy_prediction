from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # <-- Make home the root URL
    path('login/', views.user_login, name='login'),  # Move login to /login/
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('user/', views.user_home, name='user_home'),
    path('admin-home/', views.admin_home, name='admin_home'),
    path('upload/', views.upload_dataset, name='upload_dataset'),
    path('preprocess/', views.preprocess_dataset, name='preprocess_dataset'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('predict/', views.predict_view, name='predict'),
    path('user-list/', views.user_list, name='user_list'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('ml-algorithms/', views.ml_algorithms, name='ml_algorithms'),
    path('run-ml/<str:algo>/', views.run_ml, name='run_ml'),
    path('ml-algorithms/<str:algo>/', views.ml_algorithm_detail, name='ml_algorithm_detail'),
    path('ml-algorithms/best/', views.best_ml_algorithm, name='best_ml_algorithm'),
]