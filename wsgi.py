import sys
import os
from fastapi import FastAPI
from esp32frigo_api.main import app

sys.path.insert(0, '/home/esp32frigo_api/esp32frigo_api')

app = FastAPI()