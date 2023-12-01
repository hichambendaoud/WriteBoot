from . import views
from django.urls import path
from .views import *
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('', views.index, name= "index"),
    path('login_view/', views.login_view, name='login_view'),
    path('signup_view/', views.signup_view, name='signup_view'),
    path('logout', views.logoutPage , name="logout"),
    
    path('Gestion_workspaces/', views.Gestion_workspaces, name='Gestion_workspaces'),
    path('fetch_projects/', views.fetch_projects, name='fetch_projects'), 
    path('create_project/', views.create_project, name='create_project'),
    path('delete_project/<int:project_id>/', views.delete_project, name='delete_project'),

    path('workspace/<int:project_id>/', views.workspace, name='workspace'),
    path('update_project_name/<int:project_id>/', update_project_name, name='update_project_name'),
    path('start_new_conversation/', views.start_new_conversation, name='start_new_conversation'),
    # Add this new URL pattern

    path("update_profile_and_password/", views.update_profile_and_password, name="update_profile_and_password"),
   

    path('update_language/', views.update_language, name='update_language'),   
]

urlpatterns += staticfiles_urlpatterns()
