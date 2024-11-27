from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("oauth", views.oauth, name="oauth"),
    path("oauthCallback", views.oauthCallback, name="oauthCallback"),
    path("getWraps", views.getWraps, name="getWraps"),
    path("generateWrap", views.generateWrap, name="generateWrap"),
    path("getWrap", views.getWrap, name="getWrap"),
    path("contact", views.contact, name="contact"),
    path('deleteWrap', views.deleteWrap, name='deleteWrap'),

]