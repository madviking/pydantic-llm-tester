"""Google provider implementation for the new Google Gen AI SDK (google-genai)"""

import base64
import mimetypes
import os
import json
from typing import Dict, Any, Tuple, Union, Optional, List, Type
import logging

_module_logger = logging.getLogger(__name__)

# Attempt to import components from the new "google-genai" SDK.
# Assuming "pip install google-genai" makes "import google.genai" available.
NEW_GOOGLE_GENAI_SDK_AVAILABLE = False
GOOGLE_AUTH_AVAILABLE = False
# Placeholders for types that will be attempted to import
genai_sdk = None 
Part = None
HarmCategory = None
HarmBlockThreshold = None
Blob = None
GenerationConfig = None

try:
    import google.genai as sdk_alias # Use a generic alias first
    genai_sdk = sdk_alias # Assign to genai_sdk for use in the file
    NEW_GOOGLE_GENAI_SDK_AVAILABLE = True
    _module_logger.info(f"Successfully imported 'google.genai' SDK as genai_sdk (version: {getattr(genai_sdk, '__version__', 'unknown')}).")
    # Prepare a Client instance for the new API
    _GOOGLE_GENAI_CLIENT = None
    try:
        # Try to instantiate the client with API key if available
        import os
        api_key = os.environ.get("GOOGLE_API_KEY")
        if api_key:
            _GOOGLE_GENAI_CLIENT = genai_sdk.Client(api_key=api_key)
        else:
            _GOOGLE_GENAI_CLIENT = genai_sdk.Client()
        _module_logger.info("Instantiated google.genai.Client for API calls.")
    except Exception as e:
        _module_logger.error(f"Failed to instantiate google.genai.Client: {e}")
        _GOOGLE_GENAI_CLIENT = None

    # Try importing types from the new SDK. Paths are speculative.
    # Common patterns: genai_sdk.types.Part or genai_sdk.Part
    try:
        from google.genai.types import Part as ActualPart
        Part = ActualPart
        _module_logger.info("Imported Part from google.genai.types")
    except (ImportError, AttributeError): # Catch AttributeError if .types doesn't exist
        try:
            Part = genai_sdk.Part # Try direct attribute
            _module_logger.info("Imported Part directly from google.genai.Part")
        except (ImportError, AttributeError):
            _module_logger.warning("Could not import 'Part' from google.genai.types or google.genai.Part. Multimodal features may be unavailable.")
            class PartPlaceholder: # Minimal placeholder
                def __init__(self, text=None, inline_data=None): self.text = text; self.inline_data=inline_data
            Part = PartPlaceholder
    
    try:
        from google.genai.types import Blob as ActualBlob
        Blob = ActualBlob
    except (ImportError, AttributeError):
        try:
            Blob = genai_sdk.Blob
        except (ImportError, AttributeError):
            _module_logger.warning("Could not import 'Blob' type. Image processing might fail.")
            class BlobPlaceholder: 
                def __init__(self, mime_type, data): pass
            Blob = BlobPlaceholder

    try:
        from google.genai.types import HarmCategory as ActualHarmCategory, HarmBlockThreshold as ActualHarmBlockThreshold
        HarmCategory = ActualHarmCategory
        HarmBlockThreshold = ActualHarmBlockThreshold
    except (ImportError, AttributeError):
        try:
            HarmCategory = genai_sdk.HarmCategory
            HarmBlockThreshold = genai_sdk.HarmBlockThreshold
        except (ImportError, AttributeError):
            _module_logger.warning("Could not import HarmCategory/HarmBlockThreshold. Safety settings may be limited.")
            class HarmCategoryPlaceholder: HARM_CATEGORY_HATE_SPEECH=None; HARM_CATEGORY_HARASSMENT=None; HARM_CATEGORY_SEXUALLY_EXPLICIT=None; HARM_CATEGORY_DANGEROUS_CONTENT=None
            HarmCategory = HarmCategoryPlaceholder
            class HarmBlockThresholdPlaceholder: BLOCK_NONE=None
            HarmBlockThreshold = HarmBlockThresholdPlaceholder

    try:
        from google.genai.types import GenerationConfig as ActualGenerationConfig
        GenerationConfig = ActualGenerationConfig
    except (ImportError, AttributeError):
        try:
            GenerationConfig = genai_sdk.GenerationConfig
        except (ImportError, AttributeError):
            _module_logger.warning("Could not import 'GenerationConfig' type. Config might not be applied correctly.")
            class GenerationConfigPlaceholder:
                def __init__(self, **kwargs): pass
            GenerationConfig = GenerationConfigPlaceholder

except ImportError as e:
    _module_logger.error(f"Failed to import primary 'google.genai' SDK module. Google provider will be unavailable. Error: {e}")
    # NEW_GOOGLE_GENAI_SDK_AVAILABLE remains False

try:
    import google.auth
    GOOGLE_AUTH_AVAILABLE = True
except ImportError as e:
    _module_logger.error(f"Failed to import 'google.auth' SDK. Error: {e}")
    # GOOGLE_AUTH_AVAILABLE remains False

from ..base import BaseLLM, ModelConfig, BaseModel, ProviderConfig
from pydantic_llm_tester.utils.cost_manager import UsageData

class GoogleProvider(BaseLLM):
    """Provider implementation for Google Gemini API using the new Google Gen AI SDK"""
    
    def __init__(self, config: Optional[ProviderConfig] = None, llm_models: Optional[List[str]] = None):
        super().__init__(config, llm_models=llm_models)
        
        self.client_configured_status = False 
        self.part_type_available = (Part is not None and Part.__name__ != 'PartPlaceholder')
        self.safety_types_available = (HarmCategory is not None and HarmCategory.__name__ != 'HarmCategoryPlaceholder' and \
                                       HarmBlockThreshold is not None and HarmBlockThreshold.__name__ != 'HarmBlockThresholdPlaceholder')
        self.blob_type_available = (Blob is not None and Blob.__name__ != 'BlobPlaceholder')
        self.generation_config_type_available = (GenerationConfig is not None and GenerationConfig.__name__ != 'GenerationConfigPlaceholder')

        if not NEW_GOOGLE_GENAI_SDK_AVAILABLE or _GOOGLE_GENAI_CLIENT is None:
            self.logger.warning("Google Gen AI SDK ('google.genai') not available or Client could not be instantiated. Please ensure 'google-genai' is installed and API key is set.")
            return
        self.client_configured_status = True

    def _call_llm_api(self, prompt: str, system_prompt: str, model_name: str, 
                     model_config: ModelConfig, model_class: Type[BaseModel], files: Optional[List[str]] = None) -> Tuple[str, Union[Dict[str, Any], UsageData]]:
        
        if not self.client_configured_status:
            error_msg = "Google Provider not properly configured (SDK or credentials issue)."
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        is_multimodal_request = bool(files and self.supports_file_upload)

        effective_system_prompt = system_prompt or "You are a helpful AI assistant."
        schema_dict = model_class.model_json_schema()
        schema_str = json.dumps(schema_dict, indent=2)
        schema_instruction = (
            f"\n\nOutput MUST be JSON conforming to this schema:\n```json\n{schema_str}\n```"
        )

        # Prepare content parts for the new API (list of dicts)
        full_prompt_text_parts = [effective_system_prompt, schema_instruction, prompt]
        content_payload: List[dict] = []
        for text_content in full_prompt_text_parts:
            content_payload.append({"text": text_content})

        if is_multimodal_request:
            self.logger.info(f"Google provider processing files: {files}")
            for file_path in files:
                if not os.path.exists(file_path):
                    continue
                mime_type, _ = mimetypes.guess_type(file_path)
                if mime_type in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
                    with open(file_path, "rb") as f:
                        image_bytes = f.read()
                    # For google-genai >=1.0.0, image part is {"inline_data": {"mime_type": ..., "data": ...}}
                    content_payload.append({
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_bytes
                        }
                    })
                    self.logger.info(f"Added image {file_path} to Google request.")
                else:
                    self.logger.warning(f"Unsupported file type '{mime_type}' for Google GenAI.")

        self.logger.info(f"Sending request to Google model {model_name}")

        try:
            # Use the new google-genai API: call generate_content via client.models
            gen_conf_dict = {
                "temperature": 0.1,
                "max_output_tokens": model_config.max_output_tokens,
                "response_mime_type": "application/json"
            }

            # Safety settings are not yet supported in the new API as objects, so skip for now
            response = _GOOGLE_GENAI_CLIENT.models.generate_content(
                model=model_name,
                contents=content_payload,
                config=gen_conf_dict
            )

            # Extract response text
            response_text = ""
            # The new API returns response.candidates[0].content.parts[0].text for text
            try:
                candidates = getattr(response, "candidates", None)
                if candidates and hasattr(candidates[0], "content"):
                    parts = getattr(candidates[0].content, "parts", None)
                    if parts and hasattr(parts[0], "text"):
                        response_text = parts[0].text
                    elif gen_conf_dict.get("response_mime_type") == "application/json":
                        # If JSON was expected but not found in parts[0].text (e.g. content is None due to blocking)
                        self.logger.warning(f"Expected JSON response, but parts[0].text not found. Response: {response}")
                        response_text = "" # Return empty string, will fail JSON parsing downstream as expected
                    else:
                        # Fallback for non-JSON expected responses or other issues
                        response_text = str(response)
                elif gen_conf_dict.get("response_mime_type") == "application/json":
                    # If JSON was expected but candidates or content is missing
                    self.logger.warning(f"Expected JSON response, but candidates or content missing. Response: {response}")
                    response_text = "" # Return empty string
                else:
                    # Fallback for non-JSON expected responses or other issues
                    response_text = str(response)
            except Exception as e:
                self.logger.warning(f"Could not extract text from Google response: {e}")
                if gen_conf_dict.get("response_mime_type") == "application/json":
                    response_text = "" # Ensure empty string if JSON was expected
                else:
                    response_text = str(response)

            # Usage metadata (tokens)
            prompt_tokens = 0
            completion_tokens = 0
            if hasattr(response, "usage_metadata") and response.usage_metadata is not None:
                prompt_tokens = response.usage_metadata.prompt_token_count if hasattr(response.usage_metadata, "prompt_token_count") and response.usage_metadata.prompt_token_count is not None else 0
                completion_tokens = response.usage_metadata.candidates_token_count if hasattr(response.usage_metadata, "candidates_token_count") and response.usage_metadata.candidates_token_count is not None else 0
            
            # Fallback if usage_metadata is not available or tokens are still zero (e.g. not provided by API for some reason)
            # For example, if the response was blocked, token counts might be zero.
            if completion_tokens == 0 and response_text: # If API said 0 completion tokens but we have text, estimate.
                self.logger.warning(
                    f"Completion tokens from usage_metadata is zero (prompt_tokens: {prompt_tokens}), "
                    f"but response_text is present. Estimating completion_tokens from response_text length. "
                    f"Original response finish_reason: {response.candidates[0].finish_reason if response.candidates else 'N/A'}"
                )
                completion_tokens = len(response_text.split()) # Basic estimation
            elif prompt_tokens == 0 and completion_tokens == 0 and not response_text:
                 self.logger.warning(
                    f"Token counts from usage_metadata are zero and no response text. "
                    f"Finish reason: {response.candidates[0].finish_reason if response.candidates else 'N/A'}"
                 )
            # If prompt_tokens is 0, we keep it as 0 as we can't estimate it reliably here.

            usage_data = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            }

            return response_text, usage_data

        except Exception as e:
            self.logger.error(f"Error calling Google API with model {model_name}: {str(e)}", exc_info=True)
            raise ValueError(f"Error calling Google API with model {model_name}: {str(e)}")
