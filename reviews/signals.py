# reviews/signals.py
import logging
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import UserProfile, Review

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile_and_send_welcome(sender, instance, created, **kwargs):
    """
    Create a UserProfile automatically on user creation and attempt to send a welcome email.
    Errors while sending are logged.
    """
    if not created:
        return

    # create profile
    try:
        UserProfile.objects.create(user=instance)
        logger.info("UserProfile created for user=%s", instance.username)
    except Exception as exc:
        logger.exception("Failed to create UserProfile for user=%s: %s", instance.username, exc)

    # send welcome email if user has email
    if instance.email:
        subject = "Welcome to BookReview"
        message = (
            f"Hi {instance.username},\n\n"
            "Thanks for creating an account on BookReview. You can now browse books, "
            "leave reviews, and rate them.\n\n"
            "Thanks,\nThe BookReview Team"
        )
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER or "webmaster@localhost")
        try:
            send_mail(subject, message, from_email, [instance.email], fail_silently=False)
            logger.info("Welcome email sent to %s", instance.email)
        except Exception as exc:
            # Log exception but don't crash user creation flow
            logger.exception("Error sending welcome email to %s: %s", instance.email, exc)


@receiver(post_save, sender=Review)
def notify_admin_on_new_review(sender, instance, created, **kwargs):
    """
    Notify site admins (or EMAIL_HOST_USER) when a new review is created.
    Include link to the book detail page. Also attempt to notify book owner if available.
    """
    if not created:
        return

    # Prepare recipients: prefer ADMINS, else fall back to EMAIL_HOST_USER
    recipients = [a[1] for a in getattr(settings, "ADMINS", []) if len(a) > 1 and a[1]]
    if not recipients and getattr(settings, "EMAIL_HOST_USER", ""):
        recipients = [settings.EMAIL_HOST_USER]

    if not recipients:
        logger.warning(
            "No admin recipients configured; skipping admin notification for review id=%s", instance.pk
        )
        # still try to notify book owner (if exists) below
        recipients = []

    # Build absolute URL to the book detail
    site_base = getattr(settings, "SITE_URL", "http://127.0.0.1:8000").rstrip('/')
    try:
        # Prefer get_absolute_url if implemented on Book model
        book_url = instance.book.get_absolute_url()
    except Exception:
        # Fallback to named route if available
        try:
            book_url = reverse("reviews:book-detail", args=[instance.book.pk])
        except Exception:
            book_url = f"/books/{instance.book.pk}/"
    full_book_url = f"{site_base}{book_url}"

    subject = f"New review for '{instance.book.title}' (rating: {instance.rating})"
    message = (
        f"A new review has been posted on BookReview.\n\n"
        f"Book: {instance.book.title}\n"
        f"Author: {instance.book.author}\n"
        f"Rating: {instance.rating}\n"
        f"Comment: {instance.comment}\n"
        f"Reviewer: {instance.user.username} ({instance.user.email or 'no-email'})\n\n"
        f"View the book: {full_book_url}\n\n"
        f"-- BookReview notification"
    )
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER or "webmaster@localhost")

    # Send to admins (if any)
    try:
        if recipients:
            send_mail(subject, message, from_email, recipients, fail_silently=False)
            logger.info("Sent review notification for review id=%s to admins: %s", instance.pk, recipients)
    except Exception as exc:
        logger.exception("Failed to send review notification to admins for review id=%s: %s", instance.pk, exc)

    # Attempt to notify book owner if book has owner relation or owner_email attribute
    owner_emails = []

    # common patterns: Book.owner.email or Book.owner_email
    try:
        owner = getattr(instance.book, "owner", None)
        if owner and getattr(owner, "email", None):
            owner_emails.append(owner.email)
    except Exception:
        pass

    try:
        owner_email_field = getattr(instance.book, "owner_email", None)
        if owner_email_field:
            owner_emails.append(owner_email_field)
    except Exception:
        pass

    # dedupe and remove empty
    owner_emails = list({e for e in owner_emails if e})

    if owner_emails:
        try:
            send_mail(
                f"New review on your book: {instance.book.title}",
                message,
                from_email,
                owner_emails,
                fail_silently=False,
            )
            logger.info("Sent review notification to book owner(s) %s for review id=%s", owner_emails, instance.pk)
        except Exception as exc:
            logger.exception(
                "Failed to send review notification to book owner(s) %s for review id=%s: %s",
                owner_emails,
                instance.pk,
                exc,
            )
