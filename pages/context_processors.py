from django.db.models import Q

from .models import MessageContact


def _a_champ_utilisateur():
    return any(
        field.name == 'utilisateur'
        for field in MessageContact._meta.get_fields()
    )


def _est_admin(user):
    return bool(
        user.is_authenticated and (user.is_staff or user.is_superuser)
    )


def _queryset_messages_pour_utilisateur(user):
    """Retourne tous les messages pour l'admin, ou uniquement ceux de l'utilisateur."""
    if _est_admin(user):
        return MessageContact.objects.all()

    email_user = (user.email or '').strip()
    filtre = Q(email__iexact=email_user) if email_user else Q(pk__in=[])

    if _a_champ_utilisateur():
        filtre = Q(utilisateur=user) | filtre

    return MessageContact.objects.filter(filtre)


def messages_contact_context(request):
    """Compte uniquement les messages non lus pour la cloche de notification."""
    nb_messages_non_lus = 0

    if request.user.is_authenticated:
        qs_utilisateur = _queryset_messages_pour_utilisateur(request.user)

        if _est_admin(request.user):
            # Admin : messages avec lu=False (qu'ils aient été répondus ou non)
            nb_messages_non_lus = qs_utilisateur.filter(lu=False).count()
        else:
            # Client : réponses de l'atelier reçues et non encore lues
            nb_messages_non_lus = qs_utilisateur.filter(
                repondu=True,
                lu=False,
            ).count()

    return {
        'nb_messages_non_lus': nb_messages_non_lus,
    }