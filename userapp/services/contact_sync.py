from django.contrib.auth import get_user_model
from django.db import transaction

from userapp.models import Contact

User = get_user_model()


def normalize_phone(phone_number: str) -> str:
    """Return digits-only phone numbers for consistent comparisons."""
    if not phone_number:
        return ''
    return ''.join(ch for ch in str(phone_number) if ch.isdigit())


def _match_registered_user(normalized_phone: str):
    if not normalized_phone:
        return None
    return User.objects.filter(phone_number=normalized_phone).first()


def _ensure_reciprocal(owner_contact: Contact):
    other_user = owner_contact.contact_user
    if not other_user or other_user == owner_contact.owner:
        return
    normalized = normalize_phone(owner_contact.owner.phone_number)
    if not normalized:
        return
    reciprocal, _ = Contact.objects.get_or_create(
        owner=other_user,
        phone_number=normalized,
        defaults={'display_name': owner_contact.owner.username}
    )
    reciprocal.contact_user = owner_contact.owner
    reciprocal.is_mutual = True
    if not reciprocal.display_name:
        reciprocal.display_name = owner_contact.owner.username
    reciprocal.save()


@transaction.atomic
def _mark_mutual(contact: Contact):
    if contact.contact_user_id is None:
        return
    if not contact.display_name:
        contact.display_name = contact.contact_user.username
    contact.is_mutual = True
    contact.save()
    _ensure_reciprocal(contact)


def create_or_update_contact(owner, phone_number: str, display_name: str = '') -> Contact:
    normalized = normalize_phone(phone_number)
    if not normalized:
        raise ValueError('A valid phone number is required.')
    contact, _ = Contact.objects.get_or_create(
        owner=owner,
        phone_number=normalized,
        defaults={'display_name': display_name}
    )
    if display_name and not contact.display_name:
        contact.display_name = display_name
        contact.save(update_fields=['display_name'])
    return contact


def manual_contact_entry(owner, phone_number: str, display_name: str = '') -> Contact:
    contact = create_or_update_contact(owner, phone_number, display_name)
    match = _match_registered_user(contact.phone_number)
    if match:
        contact.contact_user = match
        contact.save(update_fields=['contact_user'])
        _mark_mutual(contact)
    return contact


def sync_contacts_for_user(user):
    """Link stored numbers to registered users for both directions."""
    # People who saved my number.
    normalized = normalize_phone(user.phone_number)
    if normalized:
        for contact in Contact.objects.select_for_update().filter(phone_number=normalized).exclude(owner=user):
            if contact.contact_user_id != user.id:
                contact.contact_user = user
                contact.save(update_fields=['contact_user'])
            _mark_mutual(contact)

    # Numbers I saved that now belong to registered users.
    entries = Contact.objects.select_for_update().filter(owner=user)
    numbers = [entry.phone_number for entry in entries if entry.phone_number]
    if not numbers:
        return
    user_map = {
        candidate.phone_number: candidate
        for candidate in User.objects.filter(phone_number__in=numbers)
    }
    for entry in entries:
        candidate = user_map.get(entry.phone_number)
        if candidate:
            if entry.contact_user_id != candidate.id:
                entry.contact_user = candidate
                entry.save(update_fields=['contact_user'])
            _mark_mutual(entry)
# *** End of File
