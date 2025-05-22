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
    # Main SDK import
    import google.genai as genai_sdk
    import os
    import google.auth

    NEW_GOOGLE_GENAI_SDK_AVAILABLE = True
    GOOGLE_AUTH_AVAILABLE = True

    _module_logger.info(
        f"Successfully imported 'google.genai' SDK (version: {getattr(genai_sdk, '__version__', 'unknown')}).")

    # Client instantiation
    api_key = os.environ.get("GOOGLE_API_KEY")
    _GOOGLE_GENAI_CLIENT = genai_sdk.Client(api_key=api_key) if api_key else genai_sdk.Client()
    _module_logger.info("Instantiated google.genai.Client for API calls.")

    # Import necessary types
    from google.genai.types import Part, Blob, HarmCategory, HarmBlockThreshold, GenerationConfig
except Exception as e:
    NEW_GOOGLE_GENAI_SDK_AVAILABLE = False
    _GOOGLE_GENAI_CLIENT = None
    _module_logger.error(f"Failed to set up Google GenAI SDK: {e}")

from ..base import BaseLLM, ModelConfig, BaseModel, ProviderConfig
from pydantic_llm_tester.utils.cost_manager import UsageData


"""
This is needed only for debugging, but left here as Google has been little temperemental with their API.
"""
def serialize_part(part):
    # Dump all attributes for debugging
    result = {"type": "Part"}
    try:
        for attr in dir(part):
            if not attr.startswith("_"):
                try:
                    value = getattr(part, attr)
                    # Don't dump raw image data, just its length
                    if attr == "data" and isinstance(value, (bytes, bytearray)):
                        result["data_len"] = len(value)
                    else:
                        # Try to serialize, fallback to str
                        try:
                            json.dumps(value)
                            result[attr] = value
                        except Exception:
                            result[attr] = str(value)
                except Exception as e:
                    result[attr] = f"<error: {e}>"
    except Exception as e:
        result["error"] = f"Could not serialize part: {e}"
    return result

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

        # Combine all prompt text into a single string as recommended by Gemini docs
        combined_prompt = f"{effective_system_prompt}\n{schema_instruction}\n{prompt}"

        # Use the Gemini SDK's Part class for images, and plain strings for text
        content_payload: List[Any] = []

        if is_multimodal_request:
            self.logger.info(f"Google provider processing files: {files}")
            # Try image first, then prompt (as in Gemini docs)
            for file_path in files:
                if not os.path.exists(file_path):
                    continue
                mime_type, _ = mimetypes.guess_type(file_path)
                if mime_type in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
                    with open(file_path, "rb") as f:
                        image_bytes = f.read()
                    if Part is not None and hasattr(Part, "from_bytes"):
                        image_part = Part.from_bytes(data=image_bytes, mime_type=mime_type)
                        content_payload.append(image_part)
                        self.logger.info(f"Added image {file_path} to Google request as Part.from_bytes.")
                    else:
                        self.logger.warning("Gemini SDK Part.from_bytes not available, cannot add image.")
                else:
                    self.logger.warning(f"Unsupported file type '{mime_type}' for Google GenAI.")
            content_payload.append(combined_prompt)
        else:
            # Text-only: just send the combined prompt
            content_payload.append(combined_prompt)

        self.logger.info(f"Sending request to Google model {model_name}")

        # Debug: Write a serializable version of the content payload to file
        # serializable_payload = []
        # for item in content_payload:
        #     if isinstance(item, str):
        #         serializable_payload.append({"type": "str", "value": item})
        #     else:
        #         serializable_payload.append(serialize_part(item))

        # try:
        #     with open("test_results/google_raw_content_payload.txt", "w") as f:
        #         f.write(json.dumps(serializable_payload, indent=2))
        # except Exception as e:
        #     self.logger.warning(f"Could not write content payload to file: {e}")
        #
        # print("Combined prompt:", combined_prompt)

        try:
            """
            COUPLE NOTES HERE:
            - gemini-2.5-pro-exp-03-25 would fail on RECITATION almost in all cases. Many people reporting this problem.
            - default token limits are very low
            - increasing temperature might help for RECITATION
            - general reliability has been extremely poor (11.5.2025), I expect this to be a temporary problem
            """

            # Use the new google-genai API: call generate_content via client.models
            gen_conf_dict = {
                "temperature": 0.1,
                "max_output_tokens": 20000  # PATCH: Increase output tokens for debugging
            }

            # Safety settings are not yet supported in the new API as objects, so skip for now
            response = _GOOGLE_GENAI_CLIENT.models.generate_content(
                model=model_name,
                contents=content_payload,
                config=gen_conf_dict
            )

            # put to file for debugging
            # with open("test_results/google_raw_response.txt", "w") as f:
            #     f.write("repr(response):\n")
            #     f.write(repr(response.text))
            #     f.write("\n\n")
                    
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
                        try:
                            self.logger.debug(f"Full raw response object (repr): {repr(response)}")
                            if hasattr(response, '__dict__'):
                                self.logger.debug(f"Full raw response __dict__: {response.__dict__}")
                            # Write raw response to file for debugging
                            # with open("test_results/google_raw_response.txt", "w") as f:
                            #     f.write("repr(response):\n")
                            #     f.write(repr(response))
                            #     f.write("\n\n")
                            #     if hasattr(response, '__dict__'):
                            #         f.write("response.__dict__:\n")
                            #         f.write(str(response.__dict__))
                        except Exception as e:
                            self.logger.debug(f"Could not dump full raw response: {e}")
                        response_text = "" # Return empty string, will fail JSON parsing downstream as expected
                    else:
                        # Fallback for non-JSON expected responses or other issues
                        response_text = str(response)
                elif gen_conf_dict.get("response_mime_type") == "application/json":
                    # If JSON was expected but candidates or content is missing
                    self.logger.warning(f"Expected JSON response, but candidates or content missing. Response: {response}")
                    try:
                        self.logger.debug(f"Full raw response object (repr): {repr(response)}")
                        if hasattr(response, '__dict__'):
                            self.logger.debug(f"Full raw response __dict__: {response.__dict__}")
                        # Write raw response to file for debugging
                        # with open("test_results/google_raw_response.txt", "w") as f:
                        #     f.write("repr(response):\n")
                        #     f.write(repr(response))
                        #     f.write("\n\n")
                        #     if hasattr(response, '__dict__'):
                        #         f.write("response.__dict__:\n")
                        #         f.write(str(response.__dict__))
                    except Exception as e:
                        self.logger.debug(f"Could not dump full raw response: {e}")
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
                "total_tokens": prompt_tokens + completion_tokens,
                "model": model_name # Add the model name to usage data
            }

            return response_text, usage_data

        except Exception as e:
            self.logger.error(f"Error calling Google API with model {model_name}: {str(e)}", exc_info=True)
            raise ValueError(f"Error calling Google API with model {model_name}: {str(e)}")
