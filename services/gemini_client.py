import google.generativeai as genai
import asyncio
import logging
from typing import List, Optional, Callable, Any

from config import Config

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        # Build key pool: prefer GEMINI_API_KEYS list; fallback to single GEMINI_API_KEY
        self._api_keys: List[str] = Config.GEMINI_API_KEYS or ([Config.GEMINI_API_KEY] if Config.GEMINI_API_KEY else [])
        if not self._api_keys:
            raise ValueError("No Gemini API keys provided")

        self._key_index: int = 0
        self.chat_model = Config.GEMINI_MODEL  # e.g. "gemini-1.5-flash"
        self.embedding_model = Config.GEMINI_EMBEDDING_MODEL  # e.g. "gemini-embedding-001"
        self.chat_history = []

        # Configure SDK with the first key
        genai.configure(api_key=self._api_keys[self._key_index])
        current_key = self._api_keys[self._key_index]
        masked_key = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else "***"
        logger.info(f"Initialized Gemini client with key index {self._key_index} (key: {masked_key})")
        # Prepare model instance for text generation
        self.model = genai.GenerativeModel(model_name=self.chat_model)

    def _rotate_key(self) -> None:
        self._key_index = (self._key_index + 1) % len(self._api_keys)
        genai.configure(api_key=self._api_keys[self._key_index])
        current_key = self._api_keys[self._key_index]
        masked_key = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else "***"
        logger.info(f"Rotated Gemini API key. Now using key index {self._key_index} (key: {masked_key})")

    async def _with_key_rotation(self, func: Callable[[], Any], max_attempts: Optional[int] = None) -> Any:
        """
        Execute a callable with automatic key rotation on failures that likely indicate
        quota/exhaustion. Tries up to max_attempts (defaults to number of keys).
        """
        attempts = 0
        limit = max_attempts or len(self._api_keys)
        last_error: Optional[Exception] = None
        while attempts < limit:
            try:
                return await asyncio.to_thread(func)
            except Exception as e:  # Broad catch; filter by message for quota/permission
                last_error = e
                message = str(e).lower()
                if any(token in message for token in [
                    "quota", "rate", "exceed", "permission", "api key invalid", "api key not valid", "429"
                ]):
                    current_key = self._api_keys[self._key_index]
                    masked_key = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else "***"
                    logger.critical(f"Gemini call failed (attempt {attempts+1}/{limit}) with key index {self._key_index} (key: {masked_key}): {e}. Rotating key...")
                    self._rotate_key()
                    # Recreate model after key change
                    self.model = genai.GenerativeModel(model_name=self.chat_model)
                    attempts += 1
                    continue
                # For other errors, don't rotate further
                current_key = self._api_keys[self._key_index]
                masked_key = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else "***"
                # logger.error(f"Gemini call failed with non-rotatable error using key index {self._key_index} (key: {current_key}): {e}")
                logger.error(f"Gemini call failed with non-rotatable error using key index {self._key_index} (key: {masked_key}): {e}")
                raise
        # If all attempts failed with rotatable errors
        assert last_error is not None
        raise last_error

    async def generate_response(self, query: str, context: str = "", file_context: bool = False, is_image: bool = False) -> str:
        try:
            # Note: Image processing is now handled in FileParser, so is_image should always be False here
            if context:
                prompt = self._build_file_prompt(query, context) if file_context else self._build_rag_prompt(query, context)
            elif not context and not is_image:
                prompt = self._build_normal_prompt(query)
            else:
                raise ValueError("Invalid context or image")
            
            # Use google-generativeai GenerativeModel with rotation
            response = await self._with_key_rotation(lambda: self.model.generate_content(prompt))
            
            # Extract response text based on the new API structure
            response_text = None
            
            # Debug: Log the response structure to understand the API response
            logger.debug(f"Response type: {type(response)}")
            logger.debug(f"Response attributes: {dir(response)}")
            
            # Try different ways to access the response text
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        response_text = candidate.content.parts[0].text
                    elif hasattr(candidate.content, 'text'):
                        response_text = candidate.content.text
            elif hasattr(response, 'text'):
                response_text = response.text
            elif hasattr(response, 'content'):
                if hasattr(response.content, 'parts') and response.content.parts:
                    part0 = response.content.parts[0]
                    response_text = getattr(part0, 'text', None) or getattr(response, 'text', None)
                elif hasattr(response.content, 'text'):
                    response_text = response.content.text
            elif hasattr(response, 'parts') and response.parts:
                part0 = response.parts[0]
                response_text = getattr(part0, 'text', None)
            
            if not response_text:
                logger.error(f"Could not extract response text from: {response}")
                response_text = "I couldn't generate a response."
            
            self.chat_history.append({"role": "user", "content": query})
            self.chat_history.append({"role": "assistant", "content": response_text})
            if len(self.chat_history) > 20:
                self.chat_history = self.chat_history[-20:]
            logger.info(f"Generated response for query: {query[:50]}...")
            return response_text
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise

    async def generate_response_with_image(self, prompt: str, image_data: str) -> str:
        """
        Generate response using Gemini Vision API with image
        """
        try:
            import google.generativeai as genai
            
            # Create content parts with image
            content_parts = [
                prompt,
                {
                    "mime_type": "image/jpeg",
                    "data": image_data
                }
            ]
            
            # Use google-generativeai GenerativeModel with rotation
            response = await self._with_key_rotation(lambda: self.model.generate_content(content_parts))
            
            # Extract response text
            response_text = None
            
            # Try different ways to access the response text
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        response_text = candidate.content.parts[0].text
                    elif hasattr(candidate.content, 'text'):
                        response_text = candidate.content.text
            elif hasattr(response, 'text'):
                response_text = response.text
            elif hasattr(response, 'content'):
                if hasattr(response.content, 'parts') and response.content.parts:
                    part0 = response.content.parts[0]
                    response_text = getattr(part0, 'text', None) or getattr(response, 'text', None)
                elif hasattr(response.content, 'text'):
                    response_text = response.content.text
            elif hasattr(response, 'parts') and response.parts:
                part0 = response.parts[0]
                response_text = getattr(part0, 'text', None)
            
            if not response_text:
                logger.error(f"Could not extract response text from: {response}")
                response_text = "I couldn't generate a response for the image."
            
            self.chat_history.append({"role": "user", "content": f"[Image Analysis Request]: {prompt}"})
            self.chat_history.append({"role": "assistant", "content": response_text})
            if len(self.chat_history) > 20:
                self.chat_history = self.chat_history[-20:]
            
            logger.info(f"Generated image analysis response: {len(response_text)} characters")
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating image response: {str(e)}")
            raise

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        try:
            embeddings = []
            for text in texts:
                result = await self._with_key_rotation(lambda: genai.embed_content(
                    model=self.embedding_model,
                    content=text,
                    task_type="RETRIEVAL_DOCUMENT"
                ))
                
                # Debug: Log the result structure to understand the API response
                logger.debug(f"Embedding result type: {type(result)}")
                logger.debug(f"Embedding result attributes: {dir(result)}")
                
                # Try different ways to access the embedding based on the API response structure
                emb = None
                
                # Try different ways based on SDK version
                if isinstance(result, dict):
                    # google-generativeai<=0.8 often returns dict
                    if 'embedding' in result:
                        # embedding may be a list or nested dict
                        emb_val = result['embedding']
                        if isinstance(emb_val, dict) and 'values' in emb_val:
                            emb = emb_val['values']
                        else:
                            emb = emb_val
                    elif 'embeddings' in result and result['embeddings']:
                        emb_item = result['embeddings'][0]
                        emb = emb_item.get('values', emb_item)
                else:
                    # Object-style response
                    if hasattr(result, 'embedding') and result.embedding is not None:
                        emb_attr = result.embedding
                        if isinstance(emb_attr, list) and emb_attr:
                            first = emb_attr[0]
                            emb = getattr(first, 'values', getattr(first, 'embedding', None))
                        else:
                            emb = getattr(emb_attr, 'values', emb_attr)
                    elif hasattr(result, 'embeddings') and result.embeddings:
                        first = result.embeddings[0]
                        emb = getattr(first, 'values', getattr(first, 'embedding', None))
                
                # If all methods fail, raise an error with debug info
                if emb is None:
                    logger.error(f"Could not extract embedding from result: {result}")
                    raise ValueError(f"Unable to extract embedding from API response. Result type: {type(result)}")
                
                embeddings.append(emb)
            logger.info(f"Generated embeddings for {len(texts)} texts")
            return embeddings
        except Exception as e:
            logger.error(f"Error getting embeddings: {str(e)}")
            raise
    
    def _build_rag_prompt(self, query: str, context: str) -> str:
        """
        Build a RAG prompt with context
        """
        prompt = f"""You are Pivot, an AI-powered cybersecurity and legal compliance consultant chatbot 
            for Myanmar SMEs and start-ups.

            Core Purpose:
            - Provide clear, practical guidance on Myanmar Cyber Law, PDPA, ISO 27001, and compliance requirements.
            - Help non-technical business owners improve cybersecurity awareness and digital risk management.
            - Detect and explain threats such as phishing, scams, and misconfigurations.

            Capabilities:
            - Compliance Guidance: Explain local and international privacy regulations in simple terms.
            - Threat Detection: Analyze suspicious emails, URLs, or messages for phishing/scam signs.
            - Interactive Training: Provide short, gamified awareness modules.
            - Policy Simplifier: Summarize complex legal or technical documents in plain language.
            - Risk Assessment: Offer basic tools and checklists for SMEs to assess risks.

            Style & Tone:
            - Use Burmese as primary language if user didn't mention to use another language.
            - Use clear, simple, supportive language (avoid heavy jargon).
            - Respond as a helpful consultant who empowers practical action.
            - Keep answers accurate, contextual, and Myanmar-relevant.

            Restrictions:
            - Do not provide false or misleading information.
            - If uncertain, add a caution and suggest next steps or references.
            - Avoid unrelated political discussions.

            Context:
            {context}

            User Question:
            {query}

            Answer with a clear, accurate, and helpful response based on the context above."""
                
        return prompt

    
    def _build_normal_prompt(self, query: str) -> str:
        """
        Build a normal prompt without external context
        """
        prompt = f"""You are Pivot, an AI-powered assistant for Myanmar SMEs and start-ups. 
            Answer in **Burmese** by default, unless the user specifically requests English or another language. 
            Keep responses clear, accurate, and helpful.

            User Question:
            {query}

            Provide a concise, correct, and supportive answer."""
        
        return prompt

    
    def _build_file_prompt(self, query: str, context: str) -> str:
        """
        Build a prompt specifically for file-based questions.

        This prompt instructs the AI to answer based ONLY on the provided document content.
        If the document does not contain relevant information, the AI should explicitly state that.
        """
        prompt = f"""You are a helpful AI assistant. The user is asking about a specific document.
            Please answer their question based ONLY on the content of that document provided below.

        Document Content:
        {context}

        User Question: {query}

        Provide a clear answer based on the document content. If the document doesn't contain information relevant to the question, please say so.
        """
        return prompt

        
    def clear_chat_history(self) -> None:
            """
            Clear the chat history
            """
            self.chat_history = []
            logger.info("Cleared chat history")
        
    def get_chat_history(self) -> List[dict]:
            """
            Get the current chat history
            """
            return self.chat_history.copy() 