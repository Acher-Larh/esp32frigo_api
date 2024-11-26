import sys
import os
from fastapi import FastAPI
from my_project.main import app

sys.path.insert(0, '/home/yourusername/my_project')

app = FastAPI()

# Your FastAPI routes and logic here
