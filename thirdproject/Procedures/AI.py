import os
import google.generativeai as genai

from Procedures.Storage import (
    upload_file
) 
from Settings import GEMINI_API_KEY 

def upload_to_gemini(path, mime_type=None):
  file = genai.upload_file(path, mime_type=mime_type)

  return file
   

