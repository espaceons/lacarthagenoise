from django.db import models


from django.db import models


class MessageContact(models.Model):
    nom = models.CharField("Nom complet", max_length=120)
    email = models.EmailField("Adresse email")
    telephone = models.CharField("Téléphone", max_length=30, blank=True)
    sujet = models.CharField("Sujet", max_length=150)
    message = models.TextField("Message")
    lu = models.BooleanField("Lu", default=False)
    repondu = models.BooleanField("Répondu", default=False)
    reponse = models.TextField("Réponse envoyée", blank=True)
    date_reponse = models.DateTimeField(
        "Date de réponse", null=True, blank=True)
    date_envoi = models.DateTimeField("Date d'envoi", auto_now_add=True)

    class Meta:
        verbose_name = "Message de contact"
        verbose_name_plural = "Messages de contact"
        ordering = ['-date_envoi']

    def __str__(self):
        return f"{self.sujet} — {self.nom} ({self.email})"
