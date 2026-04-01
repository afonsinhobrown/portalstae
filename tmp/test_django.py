import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
try:
    django.setup()
    print("Django setup OK!")
    from rs.models import MaterialEleitoral
    print("Models import OK!")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
