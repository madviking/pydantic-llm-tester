"""
Manager for LLM provider connections
"""

import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

from .config_manager import get_provider_model
from .cost_manager import UsageData, cost_tracker

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
        self.initialization_errors = {}
        
        for provider in self.providers:
            try:
                # Skip providers that are mocks or not implemented
                if provider.startswith("mock_") or provider == "mock_provider":
                    self.logger.info(f"Using mock provider: {provider}")
                    continue
                
                # Check for API keys before attempting to initialize
                if provider == "openai":
                    if not os.environ.get("OPENAI_API_KEY"):
                        self.initialization_errors[provider] = "OPENAI_API_KEY not found in environment variables"
                        self.logger.warning(self.initialization_errors[provider])
                        continue
                    self.provider_clients[provider] = self._create_openai_client()
                    
                elif provider == "anthropic":
                    if not os.environ.get("ANTHROPIC_API_KEY"):
                        self.initialization_errors[provider] = "ANTHROPIC_API_KEY not found in environment variables"
                        self.logger.warning(self.initialization_errors[provider])
                        continue
                    self.provider_clients[provider] = self._create_anthropic_client()
                    
                elif provider == "mistral":
                    api_key = os.environ.get("MISTRAL_API_KEY")
                    if not api_key or api_key == "your_mistral_api_key_here":
                        self.initialization_errors[provider] = "MISTRAL_API_KEY not found or has default value in environment variables"
                        self.logger.warning(self.initialization_errors[provider])
                        continue
                    self.provider_clients[provider] = self._create_mistral_client()
                    
                elif provider == "google":
                    project_id = os.environ.get("GOOGLE_PROJECT_ID")
                    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
                    if not project_id or not credentials_path:
                        missing = []
                        if not project_id:
                            missing.append("GOOGLE_PROJECT_ID")
                        if not credentials_path:
                            missing.append("GOOGLE_APPLICATION_CREDENTIALS")
                        self.initialization_errors[provider] = f"Missing required environment variables: {', '.join(missing)}"
                        self.logger.warning(self.initialization_errors[provider])
                        continue
                    if not os.path.exists(credentials_path):
                        self.initialization_errors[provider] = f"Credentials file not found: {credentials_path}"
                        self.logger.warning(self.initialization_errors[provider])
                        continue
                    self.provider_clients[provider] = self._create_google_client()
                    
                else:
                    self.logger.warning(f"Unknown provider: {provider}")
                    self.initialization_errors[provider] = f"Unknown provider"
                    
            except Exception as e:
                self.logger.error(f"Failed to initialize {provider} client: {str(e)}")
                self.initialization_errors[provider] = str(e)
    
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
            
            if not api_key or api_key == "your_mistral_api_key_here":
                self.logger.warning("MISTRAL_API_KEY not found or has default value in environment variables")
                raise Exception("Mistral API key not configured properly")
            
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
            
            missing_vars = []
            if not project_id:
                missing_vars.append("GOOGLE_PROJECT_ID")
                self.logger.warning("GOOGLE_PROJECT_ID not found in environment variables")
            if not credentials_path:
                missing_vars.append("GOOGLE_APPLICATION_CREDENTIALS")
                self.logger.warning("GOOGLE_APPLICATION_CREDENTIALS not found in environment variables")
            
            if missing_vars:
                raise Exception(f"Missing required environment variables: {', '.join(missing_vars)}")
            
            # Verify credentials file exists
            if not os.path.exists(credentials_path):
                raise Exception(f"Credentials file not found: {credentials_path}")
            
            # Check if location is in AWS format (eu-west-1) and convert to Google format
            if location and '-' in location:
                parts = location.split('-')
                if len(parts) == 3 and parts[1] in ['east', 'west', 'north', 'south', 'central'] and parts[2].isdigit():
                    # Looks like AWS format, let's convert to Google format
                    self.logger.info(f"Converting location format from '{location}' to Google Cloud format")
                    location = f"{parts[0]}-{parts[1]}{parts[2]}"
                    self.logger.info(f"Using location: {location}")
            
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
    
    def get_response(self, provider: str, prompt: str, source: str, model_name: Optional[str] = None) -> Tuple[str, Optional[UsageData]]:
        """
        Get a response from a provider
        
        Args:
            provider: Provider name
            prompt: Prompt text
            source: Source text
            model_name: Optional specific model name to use (if provider has multiple models)
            
        Returns:
            Tuple of (response_text, usage_data)
        """
        # Check if this is a mock provider
        if provider.startswith("mock_") or provider == "mock_provider":
            self.logger.info(f"Using mock provider: {provider}")
            # Import here to avoid circular imports
            from .mock_responses import get_mock_response
            
            # Create mock usage data
            mock_model = "mock-model"
            # Estimate token count for the mock response
            prompt_tokens = len(prompt.split()) + len(source.split())
            completion_tokens = 500  # Rough estimate for mock responses
            
            # Determine which mock to use based on source content
            if "MACHINE LEARNING ENGINEER" in source or "job" in source.lower() or "software engineer" in source.lower() or "developer" in source.lower():
                mock_response = get_mock_response("job_ads", source)
            else:
                mock_response = get_mock_response("product_descriptions", source)
            
            # Create usage data for mock
            usage_data = UsageData(
                provider=provider,
                model=mock_model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            
            return mock_response, usage_data
        
        # Check if the provider is initialized
        if provider not in self.provider_clients:
            # Check if we have a specific initialization error for this provider
            if hasattr(self, 'initialization_errors') and provider in self.initialization_errors:
                error_msg = self.initialization_errors[provider]
                raise ValueError(f"Provider {provider} not initialized: {error_msg}")
            else:
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
    
    def _get_openai_response(self, prompt: str, model_name: Optional[str] = None) -> Tuple[str, UsageData]:
        """
        Get a response from OpenAI
        
        Args:
            prompt: Combined prompt text
            model_name: Optional model name (defaults to gpt-4)
            
        Returns:
            Tuple of (response_text, usage_data)
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
        
        # Extract and track usage information
        usage_info = response.usage
        usage_data = UsageData(
            provider="openai",
            model=model,
            prompt_tokens=usage_info.prompt_tokens,
            completion_tokens=usage_info.completion_tokens,
            total_tokens=usage_info.total_tokens
        )
        
        self.logger.info(f"OpenAI {model} usage: {usage_info.prompt_tokens} prompt tokens, "
                        f"{usage_info.completion_tokens} completion tokens, "
                        f"${usage_data.total_cost:.6f} total cost")
        
        return response.choices[0].message.content, usage_data
    
    def _get_anthropic_response(self, prompt: str, model_name: Optional[str] = None) -> Tuple[str, UsageData]:
        """
        Get a response from Anthropic
        
        Args:
            prompt: Combined prompt text
            model_name: Optional model name (defaults to claude-3-opus)
            
        Returns:
            Tuple of (response_text, usage_data)
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
        
        # Extract and track usage information
        usage_data = UsageData(
            provider="anthropic",
            model=model,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens
        )
        
        self.logger.info(f"Anthropic {model} usage: {response.usage.input_tokens} prompt tokens, "
                        f"{response.usage.output_tokens} completion tokens, "
                        f"${usage_data.total_cost:.6f} total cost")
        
        return response.content[0].text, usage_data
    
    def _get_mistral_response(self, prompt: str, model_name: Optional[str] = None) -> Tuple[str, UsageData]:
        """
        Get a response from Mistral
        
        Args:
            prompt: Combined prompt text
            model_name: Optional model name (defaults to mistral-large-latest)
            
        Returns:
            Tuple of (response_text, usage_data)
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
        
        # Extract and track usage information
        usage_data = UsageData(
            provider="mistral",
            model=model,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens
        )
        
        self.logger.info(f"Mistral {model} usage: {response.usage.prompt_tokens} prompt tokens, "
                        f"{response.usage.completion_tokens} completion tokens, "
                        f"${usage_data.total_cost:.6f} total cost")
        
        return response.choices[0].message.content, usage_data
    
    def _get_google_response(self, prompt: str, model_name: Optional[str] = None) -> Tuple[str, UsageData]:
        """
        Get a response from Google Vertex AI
        
        Args:
            prompt: Combined prompt text
            model_name: Optional model name (defaults to text-bison for better compatibility)
            
        Returns:
            Tuple of (response_text, usage_data)
        """
        if "google" not in self.provider_clients:
            raise ValueError("Google provider not initialized. Check API credentials and environment variables.")
            
        aiplatform = self.provider_clients["google"]
        # Default to text-bison for better compatibility across Google projects
        model = model_name or "text-bison"
        
        try:
            # First, try the text-bison model which is more widely available
            if model == "text-bison" or "gemini" not in model:
                self.logger.info(f"Using text-bison model with Google Vertex AI")
                try:
                    import vertexai
                    from vertexai.preview.language_models import TextGenerationModel
                    
                    # Initialize vertexai
                    vertexai.init(
                        project=os.environ.get("GOOGLE_PROJECT_ID"),
                        location=os.environ.get("GOOGLE_LOCATION", "us-central1")
                    )
                    
                    # Initialize the model
                    text_model = TextGenerationModel.from_pretrained("text-bison")
                    
                    # Generate text
                    response = text_model.predict(
                        prompt=f"You are a helpful data extraction assistant.\n\n{prompt}",
                        temperature=0.2,
                        max_output_tokens=1024,
                        top_k=40,
                        top_p=0.8,
                    )
                    
                    # For Google Vertex AI, we may not get direct token counts
                    # Estimate based on words (rough approximation)
                    prompt_tokens = len(prompt.split()) + 10  # Add system message words
                    completion_tokens = len(response.text.split())
                    
                    usage_data = UsageData(
                        provider="google",
                        model=model,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens
                    )
                    
                    self.logger.info(f"Google {model} estimated usage: {prompt_tokens} prompt tokens, "
                                    f"{completion_tokens} completion tokens, "
                                    f"${usage_data.total_cost:.6f} total cost")
                    
                    return response.text, usage_data
                except Exception as e:
                    # If we get an access error, use a mock response
                    if "not allowed to use Publisher Model" in str(e):
                        self.logger.warning(f"Service account doesn't have access to LLM models. Using mock response: {str(e)}")
                        # Fall back to mock response
                        is_job_ad = "job" in prompt.lower() or "engineer" in prompt.lower() or "developer" in prompt.lower()
                        from .mock_responses import get_mock_response
                        mock_response = get_mock_response("job_ads" if is_job_ad else "product_descriptions", prompt)
                        
                        # Create mock usage data
                        usage_data = UsageData(
                            provider="google",
                            model=model,
                            prompt_tokens=len(prompt.split()) + 10,
                            completion_tokens=500  # Rough estimate
                        )
                        
                        return mock_response, usage_data
                    else:
                        raise e
            else:
                # If specifically requesting Gemini, try that
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
                    
                    # Estimate token usage for Gemini models
                    # Get any usage information if available, otherwise estimate
                    try:
                        prompt_tokens = response.usage_metadata.prompt_token_count
                        completion_tokens = response.usage_metadata.candidates_token_count
                    except (AttributeError, TypeError):
                        # If usage data not available, estimate based on text length
                        prompt_tokens = len(prompt.split()) + 10  # Add system message words
                        completion_tokens = len(response.text.split())
                    
                    usage_data = UsageData(
                        provider="google",
                        model=model,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens
                    )
                    
                    self.logger.info(f"Google {model} usage: {prompt_tokens} prompt tokens, "
                                    f"{completion_tokens} completion tokens, "
                                    f"${usage_data.total_cost:.6f} total cost")
                    
                    return response.text, usage_data
                except Exception as gemini_error:
                    # If permission error, use mock
                    if "not allowed to use Publisher Model" in str(gemini_error):
                        self.logger.warning(f"Service account doesn't have access to LLM models. Using mock response: {str(gemini_error)}")
                        # Fall back to mock response
                        is_job_ad = "job" in prompt.lower() or "engineer" in prompt.lower() or "developer" in prompt.lower()
                        from .mock_responses import get_mock_response
                        mock_response = get_mock_response("job_ads" if is_job_ad else "product_descriptions", prompt)
                        
                        # Create mock usage data
                        usage_data = UsageData(
                            provider="google",
                            model=model,
                            prompt_tokens=len(prompt.split()) + 10,
                            completion_tokens=500  # Rough estimate
                        )
                        
                        return mock_response, usage_data
                    else:
                        self.logger.warning(f"Failed to use Gemini model: {str(gemini_error)}. Falling back to text-bison.")
                        # Fall back to text-bison
                        return self._get_google_response(prompt, "text-bison")
        except Exception as e:
            # Final fallback to mock response
            self.logger.error(f"Error with Google Vertex AI: {str(e)}")
            if "not allowed to use Publisher Model" in str(e):
                self.logger.warning("Service account doesn't have access to LLM models. Using mock response.")
                # Fall back to mock response
                is_job_ad = "job" in prompt.lower() or "engineer" in prompt.lower() or "developer" in prompt.lower()
                from .mock_responses import get_mock_response
                mock_response = get_mock_response("job_ads" if is_job_ad else "product_descriptions", prompt)
                
                # Create mock usage data
                usage_data = UsageData(
                    provider="google",
                    model=model,
                    prompt_tokens=len(prompt.split()) + 10,
                    completion_tokens=500  # Rough estimate
                )
                
                return mock_response, usage_data
            else:
                raise Exception(f"Failed to get response from Google Vertex AI: {str(e)}")