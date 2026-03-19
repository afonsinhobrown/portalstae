import os
import subprocess
import json

# Define the environment for local sqlite
env_sqlite = os.environ.copy()
env_sqlite['DJANGO_SETTINGS_MODULE'] = 'portalstae.settings'
env_sqlite['PYTHONUTF8'] = '1'

# Define the environment for neon
env_neon = os.environ.copy()
env_neon['DJANGO_SETTINGS_MODULE'] = 'portalstae.settings_neon'
env_neon['PYTHONUTF8'] = '1'

print("Dumping data from SQLite...")
dump_cmd = [
    "venv\\Scripts\\python.exe", "manage.py", "dumpdata",
    "--exclude", "dfec.resultadoeleitoral",
    "--exclude", "auth",
    "--exclude", "contenttypes",
    "--exclude", "sessions",
    "--exclude", "admin",
    "--indent", "2",
    "-o", "small_data.json"
]
result = subprocess.run(dump_cmd, env=env_sqlite, capture_output=True, text=True)
if result.returncode != 0:
    print("Error dumping data:")
    print(result.stderr)
    exit(1)

# Check size
size = os.path.getsize('small_data.json')
print(f"Dumped data successfully. File size: {size / 1024:.2f} KB")

print("Loading data into Neon PostgreSQL...")
load_cmd = [
    "venv\\Scripts\\python.exe", "manage.py", "loaddata", "small_data.json"
]
result_load = subprocess.run(load_cmd, env=env_neon, capture_output=True, text=True)
if result_load.returncode != 0:
    print("Error loading data:")
    print(result_load.stderr)
else:
    print("Data loaded successfully!")
    print(result_load.stdout)
