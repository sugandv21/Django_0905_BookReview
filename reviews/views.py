import logging
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View
)
from django.core.mail import send_mail
from django.conf import settings

from .forms import BookSearchForm, ReviewForm, SignupForm
from .models import Book, Review

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = "reviews/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_books"] = Book.objects.all()[:3]
        return context


class BookListView(ListView):
    model = Book
    template_name = "reviews/book_list.html"
    paginate_by = 6
    context_object_name = "books"

    def get_queryset(self):
        qs = super().get_queryset().prefetch_related("categories")
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(author__icontains=q)).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = BookSearchForm(self.request.GET)
        return context


class BookDetailView(DetailView):
    model = Book
    template_name = "reviews/book_detail.html"
    context_object_name = "book"


class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = "reviews/review_form.html"

    def dispatch(self, request, *args, **kwargs):
        # Ensure book exists
        self.book = get_object_or_404(Book, pk=kwargs.get("book_pk"))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.book = self.book
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Review added successfully.")
        return response

    def get_success_url(self):
        return reverse("reviews:book-detail", args=[self.book.pk])


class ReviewUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Review
    form_class = ReviewForm
    template_name = "reviews/review_form.html"

    def get_object(self, queryset=None):
        return get_object_or_404(Review, pk=self.kwargs.get("pk"))

    def test_func(self):
        review = self.get_object()
        return self.request.user == review.user

    def form_valid(self, form):
        messages.success(self.request, "Review updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("reviews:book-detail", args=[self.object.book.pk])


class ReviewDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Review
    template_name = "reviews/review_confirm_delete.html"

    def get_object(self, queryset=None):
        return get_object_or_404(Review, pk=self.kwargs.get("pk"))

    def test_func(self):
        review = self.get_object()
        return self.request.user.is_staff or (self.request.user == review.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Review deleted successfully.")
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("reviews:book-list")


class SignupView(View):
    """
    Signup view that creates the user and attempts to send a welcome email.
    Any email-sending errors are caught, logged, and a message is shown to the user.
    """
    template_name = "registration/signup.html"

    def get(self, request):
        form = SignupForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Attempt to send welcome email and surface outcome via messages
            from_email = getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER or "webmaster@localhost")
            if user.email:
                subject = "Welcome to BookReview"
                message = (
                    f"Hi {user.username},\n\n"
                    "Thanks for registering at BookReview. You can now browse books, leave reviews, and rate them.\n\n"
                    "Thanks,\nThe BookReview Team"
                )
                try:
                    send_mail(subject, message, from_email, [user.email], fail_silently=False)
                    messages.success(request, "Account created. A welcome email was sent to your address.")
                    logger.info("Welcome email sent to %s", user.email)
                except Exception as e:
                    # log exception and inform user that account was created but email failed
                    logger.exception("Failed to send welcome email to %s: %s", user.email, e)
                    messages.warning(request, "Account created, but we couldn't send a welcome email at this time.")
            else:
                messages.success(request, "Account created. (No email address provided.)")

            return redirect("login")
        # invalid form
        return render(request, self.template_name, {"form": form})

class BookListView(ListView):
    model = Book
    template_name = "reviews/book_list.html"
    context_object_name = "books"
    paginate_by = 3 

    def get_queryset(self):
        qs = super().get_queryset().prefetch_related("categories")
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(author__icontains=q)).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = BookSearchForm(self.request.GET)
        return context
