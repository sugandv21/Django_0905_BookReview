from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('books/', views.BookListView.as_view(), name='book-list'),
    path('books/<int:pk>/', views.BookDetailView.as_view(), name='book-detail'),
    path('books/<int:book_pk>/reviews/add/', views.ReviewCreateView.as_view(), name='review-add'),
    path('reviews/<int:pk>/edit/', views.ReviewUpdateView.as_view(), name='review-edit'),
    path('reviews/<int:pk>/delete/', views.ReviewDeleteView.as_view(), name='review-delete'),
    path('signup/', views.SignupView.as_view(), name='signup'),
]
