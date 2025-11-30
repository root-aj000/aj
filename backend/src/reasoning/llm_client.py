"""
LLM Client

Handles all interactions with Google Gemini API.
"""

from typing import List, Dict, Any, Optional, Generator
import logging
import time

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    print("Warning: google-generativeai not installed")

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client for Google Gemini API with rate limiting and error handling.
    """
    
    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.0-flash-exp",
        fallback_model: str = "gemini-1.5-pro",
        max_output_tokens: int = 8192
    ):
        """
        Initialize LLM client.
        
        Args:
            api_key: Gemini API key
            model_name: Primary model name
            fallback_model: Fallback model for tier escalation
            max_output_tokens: Maximum tokens in response
        """
        if not HAS_GENAI:
            raise RuntimeError("google-generativeai not installed")
        
        genai.configure(api_key=api_key)
        
        self.model_name = model_name
        self.fallback_model = fallback_model
        self.max_output_tokens = max_output_tokens
        
        # Initialize models
        self.model = genai.GenerativeModel(model_name)
        self.fallback = genai.GenerativeModel(fallback_model)
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
        logger.info(f"Initialized LLM client with model: {model_name}")
    
    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        
        self.last_request_time = time.time()
    
    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        use_fallback: bool = False,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: User prompt
            system_instruction: Optional system instruction
            temperature: Sampling temperature
            use_fallback: Whether to use fallback model
            max_retries: Maximum retry attempts
        
        Returns:
            Response dictionary with text and metadata
        """
        self._rate_limit()
        
        model = self.fallback if use_fallback else self.model
        model_name = self.fallback_model if use_fallback else self.model_name
        
        generation_config = {
            'temperature': temperature,
            'max_output_tokens': self.max_output_tokens,
        }
        
        # Build messages
        messages = []
        
        if system_instruction:
            messages.append({
                'role': 'system',
                'parts': [system_instruction]
            })
        
        messages.append({
            'role': 'user',
            'parts': [prompt]
        })
        
        # Try generation with retries
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Generating with {model_name} (attempt {attempt + 1}/{max_retries})")
                
                start_time = time.time()
                
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                elapsed = time.time() - start_time
                
                # Extract response
                text = response.text
                
                # Get token counts if available
                try:
                    usage = {
                        'prompt_tokens': response.usage_metadata.prompt_token_count,
                        'completion_tokens': response.usage_metadata.candidates_token_count,
                        'total_tokens': response.usage_metadata.total_token_count
                    }
                except AttributeError:
                    usage = {'total_tokens': 0}
                
                logger.info(f"Generated {usage.get('completion_tokens', 0)} tokens in {elapsed:.2f}s")
                
                return {
                    'text': text,
                    'model': model_name,
                    'usage': usage,
                    'elapsed_ms': int(elapsed * 1000),
                    'success': True
                }
            
            except Exception as e:
                last_error = e
                logger.warning(f"Generation attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        # All retries failed
        logger.error(f"Generation failed after {max_retries} attempts: {last_error}")
        
        return {
            'text': '',
            'model': model_name,
            'usage': {'total_tokens': 0},
            'elapsed_ms': 0,
            'success': False,
            'error': str(last_error)
        }
    
    def generate_streaming(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7
    ) -> Generator[str, None, None]:
        """
        Generate a streaming response.
        
        Args:
            prompt: User prompt
            system_instruction: Optional system instruction
            temperature: Sampling temperature
        
        Yields:
            Chunks of generated text
        """
        self._rate_limit()
        
        generation_config = {
            'temperature': temperature,
            'max_output_tokens': self.max_output_tokens,
        }
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        
        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            yield f"Error: {str(e)}"
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count
        
        Returns:
            Token count
        """
        try:
            result = self.model.count_tokens(text)
            return result.total_tokens
        except Exception as e:
            logger.warning(f"Token counting failed: {e}")
            # Fallback: rough approximation (4 chars per token)
            return len(text) // 4
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Multi-turn chat conversation.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
        
        Returns:
            Response dictionary
        """
        # Convert messages to Gemini format
        history = []
        
        for msg in messages[:-1]:  # All but last
            role = 'model' if msg['role'] == 'assistant' else 'user'
            history.append({
                'role': role,
                'parts': [msg['content']]
            })
        
        # Start chat with history
        chat = self.model.start_chat(history=history)
        
        # Send last message
        last_msg = messages[-1]
        
        try:
            response = chat.send_message(
                last_msg['content'],
                generation_config={'temperature': temperature}
            )
            
            return {
                'text': response.text,
                'model': self.model_name,
                'success': True
            }
        
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            
            return {
                'text': '',
                'model': self.model_name,
                'success': False,
                'error': str(e)
            }


def main():
    """CLI entry point."""
    import sys
    from ..app.config import get_settings
    
    if len(sys.argv) < 2:
        print("Usage: python llm_client.py '<prompt>'")
        sys.exit(1)
    
    prompt = sys.argv[1]
    
    settings = get_settings()
    
    client = LLMClient(
        api_key=settings.gemini_api_key,
        model_name=settings.llm_model_type
    )
    
    print(f"\n🤖 Generating response with {client.model_name}...")
    
    response = client.generate(prompt)
    
    if response['success']:
        print(f"\n✅ Response:\n{response['text']}\n")
        print(f"📊 Usage: {response['usage']}")
        print(f"⏱️  Time: {response['elapsed_ms']}ms")
    else:
        print(f"\n❌ Generation failed: {response.get('error')}")


if __name__ == "__main__":
    main()
