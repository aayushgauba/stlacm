import os
import sys

sys.path.insert(0, "/home/stlhosting/stlacm")
os.chdir("/home/stlhosting/stlacm")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stlacm.settings")

from stlacm.wsgi import application
