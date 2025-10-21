# devis/templatetags/devis_extras.py
from django import template

register = template.Library()
DEVIS_SESSION_KEY = 'devis_panier'


@register.simple_tag(takes_context=True)
def devis_count(context):
    """Retourne le nombre total d'articles uniques dans la liste de devis."""
    request = context['request']
    devis_panier = request.session.get(DEVIS_SESSION_KEY)

    if devis_panier:
        # On retourne le nombre de clés (produits uniques) dans le panier
        return len(devis_panier)
    return 0

# Alternativement, pour le nombre total de PIÈCES:
# @register.simple_tag(takes_context=True)
# def devis_total_items(context):
#     request = context['request']
#     devis_panier = request.session.get(DEVIS_SESSION_KEY, {})
#     return sum(item['quantite'] for item in devis_panier.values())
