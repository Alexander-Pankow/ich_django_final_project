from django.utils.translation import gettext_lazy as _

# Housing type options for listings: apartment, house, studio
# Варианты типов жилья: квартира, дом, студия
HOUSING_TYPE_CHOICES = [
    ('apartment', _('Apartment')),
    ('house', _('House')),
    ('studio', _('Studio')),
]