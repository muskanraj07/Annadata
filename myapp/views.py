from django.shortcuts import render
from django.conf import settings
from django.views.generic import TemplateView
from groq import Groq
import requests
import base64
from groq import Groq  # Import the Groq library
from typing import Optional
import os
from django.core.files.storage import default_storage

from django.shortcuts import render
from django.conf import settings
from groq import Groq
import base64
import os

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import os
from groq import Groq
from typing import Optional
import requests

from django.conf import settings
import os
from groq import Groq
from typing import Optional

from django.shortcuts import render
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import os
from django.shortcuts import render
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import os
from groq import Groq
from typing import Optional
import logging

from django.shortcuts import render
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from groq import Groq
import os
import logging

logger = logging.getLogger(__name__)

class GroqChatbot:
    def __init__(self, groq_api_key: Optional[str] = None):
        self.groq_client = None
        groq_key = groq_api_key or os.getenv("GROQ_API_KEY") or getattr(settings, 'GROQ_API_KEY', None)
        try:
            self.groq_client = Groq(api_key=groq_key)
        except Exception as e:
            logger.error(f"Groq client initialization failed: {e}")

        self.groq_models = {
            'powerful': 'llama3-70b-8192',
            'balanced': 'llama3-8b-8192',
            'fast': 'mixtral-8x7b-32768'
        }

    def get_response(self, prompt: str, model_type: str = 'balanced') -> Optional[str]:
        if not self.groq_client:
            return "Error: Groq client not initialized."

        if model_type not in self.groq_models:
            model_type = 'balanced'

        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=self.groq_models[model_type],
                temperature=0.7,
                max_tokens=500  # Adjust as needed
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating Groq response: {e}")
            return f"Error generating response: {e}"

@csrf_exempt
def chatbot_view(request):
    chatbot = GroqChatbot(groq_api_key=getattr(settings, 'GROQ_API_KEY', None))
    response = None
    user_prompt = request.POST.get('user_prompt')

    if request.method == 'POST' and user_prompt:
        response = chatbot.get_response(user_prompt)

    return render(request, 'myapp/chatbot.html', {
        'response': response,
    })



logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self, groq_api_key: Optional[str] = None):
        self.groq_client = None
        groq_key = groq_api_key or os.getenv("GROQ_API_KEY") or getattr(settings, 'GROQ_API_KEY', None)
        try:
            self.groq_client = Groq(api_key=groq_key)
        except Exception as e:
            logger.warning(f"Groq initialization failed - {str(e)}")

        self.groq_models = {
            'powerful': 'llama3-70b-8192',
            'balanced': 'llama3-8b-8192',
            'fast': 'mixtral-8x7b-32768'
        }

    def transcribe_audio(self, audio_path: str) -> Optional[str]:
        if not self.groq_client:
            logger.error("Groq client not initialized for transcription.")
            return None
        try:
            with open(audio_path, "rb") as audio_file:
                transcript = self.groq_client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3-turbo",  # Check Groq documentation for available STT models
                )
            return transcript.text
        except Exception as e:
            logger.error(f"Groq Speech-to-Text error: {e}")
            return None

    def process_transcript(self, text: str, model_type: str = 'balanced') -> str:
        if not self.groq_client:
            logger.error("Groq client not initialized for text processing.")
            return "Error: Groq client not initialized"
        if model_type not in self.groq_models:
            model_type = 'balanced'
        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes audio transcripts."},
                    {"role": "user", "content": f"Analyze this transcript:\n\n{text}"}
                ],
                model=self.groq_models[model_type],
                temperature=0.7,
                max_tokens=1024
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error processing with Groq: {e}")
            return f"Error processing with Groq: {e}"

    def audio_to_analysis(self, audio_path: str, model_type: str = 'balanced') -> dict:
        if not os.path.exists(audio_path):
            return {"error": "Audio file not found", "transcript": None, "analysis": None}
        transcript = self.transcribe_audio(audio_path)
        if not transcript:
            return {"error": "Transcription failed", "transcript": None, "analysis": None}
        analysis = self.process_transcript(transcript, model_type)
        return {
            "transcript": transcript,
            "analysis": analysis,
            "model_used": self.groq_models.get(model_type, 'balanced'),
            "error": None
        }

@csrf_exempt
def audio_analysis_view(request):
    analysis_result = None
    error_message = None

    processor = AudioProcessor(groq_api_key=getattr(settings, 'GROQ_API_KEY', None))

    if request.method == 'POST' and request.FILES.get('audio_upload'):
        audio_file = request.FILES['audio_upload']
        audio_path = f"temp_audio_{audio_file.name}"
        try:
            with open(audio_path, 'wb+') as destination:
                for chunk in audio_file.chunks():
                    destination.write(chunk)
            result = processor.audio_to_analysis(audio_path)
            analysis_result = result
        except Exception as e:
            error_message = f"An error occurred during audio processing: {e}"
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)

    return render(request, 'myapp/audio_analysis.html', {
        'analysis_result': analysis_result,
        'error_message': error_message,
    })

def encode_image(image_file):
    """Encodes an InMemoryUploadedFile to base64."""
    return base64.b64encode(image_file.read()).decode('utf-8')

def image_description_view(request):
    description = None
    error_message = None

    if request.method == 'POST' and request.FILES.get('image_upload'):
        uploaded_image = request.FILES['image_upload']

        try:
            base64_image = encode_image(uploaded_image)

            client = Groq(api_key=settings.GROQ_API_KEY)

            chat_completion = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What's in this image?"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{uploaded_image.content_type};base64,{base64_image}",
                                },
                            },
                        ],
                    }
                ],
            )

            if chat_completion.choices and len(chat_completion.choices) > 0 and chat_completion.choices[0].message:
                description = chat_completion.choices[0].message.content
            else:
                error_message = "Error: Could not get image description from Groq API."

        except Exception as e:
            error_message = f"An unexpected error occurred: {e}"

    elif request.method == 'POST':
        error_message = "Please upload an image."

    return render(request, 'myapp/image_description.html', {
        'description': description,
        'error_message': error_message,
    })

# Create your views here.
def index(request):
    return render(request, 'myapp/index.html')

# def audio_view(request):
#     return render(request, 'text.html')

def audio_as(request):
    return render(request, 'myapp/text.html')




