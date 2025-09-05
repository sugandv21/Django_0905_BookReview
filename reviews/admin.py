from django.contrib import admin
from .models import Book, Review, Category




@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author')
    search_fields = ('title', 'author')
    list_filter = ('author', 'categories')




@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'rating', 'created_at')
    search_fields = ('book__title', 'user__username')
    list_filter = ('rating', 'created_at')




@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)