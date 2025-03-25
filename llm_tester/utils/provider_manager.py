"""
Manager for LLM provider connections
"""

import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv


# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class ProviderManager:
    """
    Manages connections to LLM providers
    """
    
    def __init__(self, providers: List[str]):
        """
        Initialize the provider manager
        
        Args:
            providers: List of provider names to initialize
        """
        self.providers = providers
        self.logger = logging.getLogger(__name__)
        self._initialize_providers()
    
    def _initialize_providers(self) -> None:
        """Initialize connections to providers"""
        self.provider_clients = {}
        
        for provider in self.providers:
            try:
                if provider == "openai":
                    self.provider_clients[provider] = self._create_openai_client()
                elif provider == "anthropic":
                    self.provider_clients[provider] = self._create_anthropic_client()
                elif provider == "mistral":
                    self.provider_clients[provider] = self._create_mistral_client()
                elif provider == "google":
                    self.provider_clients[provider] = self._create_google_client()
                else:
                    self.logger.warning(f"Unknown provider: {provider}")
            except Exception as e:
                self.logger.error(f"Failed to initialize {provider} client: {str(e)}")
    
    def _create_openai_client(self) -> Any:
        """
        Create an OpenAI client
        
        Returns:
            OpenAI client object
        """
        try:
            import openai
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                self.logger.warning("OPENAI_API_KEY not found in environment variables")
            
            return openai.OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("OpenAI package not installed. Run 'pip install openai'")
        except Exception as e:
            raise Exception(f"Failed to initialize OpenAI client: {str(e)}")
    
    def _create_anthropic_client(self) -> Any:
        """
        Create an Anthropic client
        
        Returns:
            Anthropic client object
        """
        try:
            import anthropic
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                self.logger.warning("ANTHROPIC_API_KEY not found in environment variables")
            
            return anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("Anthropic package not installed. Run 'pip install anthropic'")
        except Exception as e:
            raise Exception(f"Failed to initialize Anthropic client: {str(e)}")
    
    def _create_mistral_client(self) -> Any:
        """
        Create a Mistral client
        
        Returns:
            Mistral client object
        """
        try:
            import mistralai.client
            api_key = os.environ.get("MISTRAL_API_KEY")
            if not api_key:
                self.logger.warning("MISTRAL_API_KEY not found in environment variables")
            
            return mistralai.client.MistralClient(api_key=api_key)
        except ImportError:
            raise ImportError("Mistral AI package not installed. Run 'pip install mistralai'")
        except Exception as e:
            raise Exception(f"Failed to initialize Mistral client: {str(e)}")
    
    def _create_google_client(self) -> Any:
        """
        Create a Google Vertex AI client
        
        Returns:
            Google Vertex AI client object
        """
        try:
            # Check for required environment variables
            project_id = os.environ.get("GOOGLE_PROJECT_ID")
            location = os.environ.get("GOOGLE_LOCATION", "us-central1")
            credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            
            if not project_id:
                self.logger.warning("GOOGLE_PROJECT_ID not found in environment variables")
            if not credentials_path:
                self.logger.warning("GOOGLE_APPLICATION_CREDENTIALS not found in environment variables")
            
            # Import vertex_ai
            from google.cloud import aiplatform
            
            # Initialize the Vertex AI SDK
            aiplatform.init(project=project_id, location=location)
            
            # We return the aiplatform module itself since we'll use it to create model instances
            return aiplatform
        except ImportError:
            raise ImportError("Google Cloud AI Platform package not installed. Run 'pip install google-cloud-aiplatform'")
        except Exception as e:
            raise Exception(f"Failed to initialize Google Vertex AI client: {str(e)}")
    
    def get_response(self, provider: str, prompt: str, source: str, model_name: Optional[str] = None) -> str:
        """
        Get a response from a provider
        
        Args:
            provider: Provider name
            prompt: Prompt text
            source: Source text
            model_name: Optional specific model name to use (if provider has multiple models)
            
        Returns:
            Response text
        """
        if provider not in self.provider_clients:
            raise ValueError(f"Provider {provider} not initialized")
        
        combined_prompt = f"{prompt}\n\nSOURCE:\n{source}"
        
        if provider == "openai":
            return self._get_openai_response(combined_prompt, model_name)
        elif provider == "anthropic":
            return self._get_anthropic_response(combined_prompt, model_name)
        elif provider == "mistral":
            return self._get_mistral_response(combined_prompt, model_name)
        elif provider == "google":
            return self._get_google_response(combined_prompt, model_name)
        else:
            raise ValueError(f"Getting responses from provider {provider} not implemented")
    
    def _get_openai_response(self, prompt: str, model_name: Optional[str] = None) -> str:
        """
        Get a response from OpenAI
        
        Args:
            prompt: Combined prompt text
            model_name: Optional model name (defaults to gpt-4)
            
        Returns:
            Response text
        """
        client = self.provider_clients["openai"]
        model = model_name or "gpt-4"
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful data extraction assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    
    def _get_anthropic_response(self, prompt: str, model_name: Optional[str] = None) -> str:
        """
        Get a response from Anthropic
        
        Args:
            prompt: Combined prompt text
            model_name: Optional model name (defaults to claude-3-opus)
            
        Returns:
            Response text
        """
        client = self.provider_clients["anthropic"]
        model = model_name or "claude-3-opus-20240229"
        
        response = client.messages.create(
            model=model,
            max_tokens=4000,
            system="You are a helpful data extraction assistant.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    
    def _get_mistral_response(self, prompt: str, model_name: Optional[str] = None) -> str:
        """
        Get a response from Mistral
        
        Args:
            prompt: Combined prompt text
            model_name: Optional model name (defaults to mistral-large-latest)
            
        Returns:
            Response text
        """
        client = self.provider_clients["mistral"]
        model = model_name or "mistral-large-latest"
        
        response = client.chat(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful data extraction assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    
    def _get_google_response(self, prompt: str, model_name: Optional[str] = None) -> str:
        """
        Get a response from Google Vertex AI
        
        Args:
            prompt: Combined prompt text
            model_name: Optional model name (defaults to gemini-pro)
            
        Returns:
            Response text
        """
        aiplatform = self.provider_clients["google"]
        model = model_name or "gemini-pro"
        
        try:
            from vertexai.generative_models import GenerativeModel, Part

            # Initialize the model
            generation_model = GenerativeModel(model)
            
            # Create the prompt - Gemini uses different prompt format
            response = generation_model.generate_content(
                [
                    Part.from_text("You are a helpful data extraction assistant."),
                    Part.from_text(prompt)
                ]
            )
            
            return response.text
        except Exception as e:
            self.logger.error(f"Error with Google Vertex AI: {str(e)}")
            raise Exception(f"Failed to get response from Google Vertex AI: {str(e)}")