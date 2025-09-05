from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse


User = settings.AUTH_USER_MODEL


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)


def __str__(self):
    return self.name




class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    categories = models.ManyToManyField(Category, related_name='books', blank=True)


def __str__(self):
    return f"{self.title} — {self.author}"


def get_absolute_url(self):
    return reverse('reviews:book-detail', args=[self.pk])


def average_rating(self):
    reviews = self.reviews.all()
    if not reviews.exists():
        return None
        return reviews.aggregate(models.Avg('rating'))['rating__avg']


class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Meta:
    ordering = ['-created_at']
    unique_together = ('book', 'user')


def __str__(self):
    return f"{self.book.title} review by {self.user} — {self.rating}"




class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)


def __str__(self):
    return f"Profile: {self.user.username}"