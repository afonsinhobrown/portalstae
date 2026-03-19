
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from ugea.models import Contrato, ItemContrato
from ugea.forms import ItemContratoFormSet

contrato = Contrato.objects.first()
formset = ItemContratoFormSet(instance=contrato)
print(f"Prefix: {formset.prefix}")
