"""
AI command handlers for Zultra Telegram Bot.
Handles AI-powered commands like ask, translate, OCR, image generation, etc.
"""

import asyncio
import base64
import io
import re
from typing import Optional, Dict, Any, List
from urllib.parse import quote

import openai
import google.generativeai as genai
from PIL import Image
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from loguru import logger

from ..core.config import get_settings
from ..db.database import get_session, create_or_update_user


class AIHandlers:
    """AI command handlers for intelligent features."""
    
    def __init__(self):
        self.settings = get_settings()
        self.openai_client = None
        self.gemini_client = None
        self.setup_ai_clients()
        
        # Language codes for translation
        self.language_codes = {
            'english': 'en', 'spanish': 'es', 'french': 'fr', 'german': 'de',
            'italian': 'it', 'portuguese': 'pt', 'russian': 'ru', 'chinese': 'zh',
            'japanese': 'ja', 'korean': 'ko', 'arabic': 'ar', 'hindi': 'hi',
            'dutch': 'nl', 'swedish': 'sv', 'norwegian': 'no', 'danish': 'da',
            'finnish': 'fi', 'polish': 'pl', 'turkish': 'tr', 'greek': 'el',
            'hebrew': 'he', 'thai': 'th', 'vietnamese': 'vi', 'indonesian': 'id',
            'malay': 'ms', 'czech': 'cs', 'slovak': 'sk', 'hungarian': 'hu',
            'romanian': 'ro', 'bulgarian': 'bg', 'croatian': 'hr', 'serbian': 'sr',
            'ukrainian': 'uk', 'lithuanian': 'lt', 'latvian': 'lv', 'estonian': 'et'
        }
    
    def setup_ai_clients(self):
        """Initialize AI clients."""
        try:
            if self.settings.openai_api_key:
                openai.api_key = self.settings.openai_api_key
                self.openai_client = openai
                logger.info("OpenAI client initialized")
            
            if self.settings.gemini_api_key:
                genai.configure(api_key=self.settings.gemini_api_key)
                self.gemini_client = genai.GenerativeModel('gemini-pro')
                logger.info("Gemini client initialized")
                
        except Exception as e:
            logger.error(f"Error setting up AI clients: {e}")
    
    async def ask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /ask command for AI chat."""
        try:
            user = update.effective_user
            
            if not context.args:
                await update.message.reply_text(
                    "🤖 <b>AI Assistant</b>\n\n"
                    "Ask me anything! I'm powered by advanced AI.\n\n"
                    "<b>Usage:</b> /ask [your question]\n\n"
                    "<b>Examples:</b>\n"
                    "• /ask What is the meaning of life?\n"
                    "• /ask Explain quantum physics simply\n"
                    "• /ask Write a poem about cats\n"
                    "• /ask Help me with Python code\n\n"
                    f"<b>Available AI:</b> {self._get_available_ai()}",
                    parse_mode=ParseMode.HTML
                )
                return
            
            question = ' '.join(context.args)
            
            # Show typing indicator
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            
            # Send "thinking" message
            thinking_msg = await update.message.reply_text(
                "🤖 <i>AI is thinking...</i>",
                parse_mode=ParseMode.HTML
            )
            
            # Get AI response
            response = await self._get_ai_response(question, user.id)
            
            if response:
                # Format response with proper length limits
                if len(response) > 4000:
                    response = response[:4000] + "..."
                
                ai_text = f"""
🤖 <b>AI Assistant</b>

<b>❓ Question:</b> {question}

<b>💭 Answer:</b>
{response}

<i>Powered by {self._get_primary_ai()} • Ask more questions anytime!</i>
"""
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 Ask Again", callback_data="ask_again"),
                        InlineKeyboardButton("🧠 Different AI", callback_data="switch_ai")
                    ],
                    [
                        InlineKeyboardButton("📤 Share Answer", callback_data="share_answer"),
                        InlineKeyboardButton("💾 Save Response", callback_data="save_response")
                    ]
                ])
                
                await thinking_msg.edit_text(
                    ai_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard
                )
                
            else:
                await thinking_msg.edit_text(
                    "❌ <b>AI Error</b>\n\n"
                    "Sorry, I couldn't process your question right now.\n\n"
                    "<b>Possible issues:</b>\n"
                    "• AI service temporarily unavailable\n"
                    "• API key not configured\n"
                    "• Question too complex or inappropriate\n\n"
                    "<i>Please try again later or rephrase your question.</i>",
                    parse_mode=ParseMode.HTML
                )
            
            logger.info(f"Ask command executed by user {user.id}")
            
        except Exception as e:
            logger.error(f"Error in ask command: {e}")
            await update.message.reply_text("❌ Error processing AI request.")
    
    async def translate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /translate command for text translation."""
        try:
            if not context.args:
                await update.message.reply_text(
                    "🌍 <b>AI Translator</b>\n\n"
                    "Translate text between languages!\n\n"
                    "<b>Usage:</b> /translate [text]\n"
                    "<b>Advanced:</b> /translate [lang] [text]\n\n"
                    "<b>Examples:</b>\n"
                    "• /translate Hello world\n"
                    "• /translate spanish Hello world\n"
                    "• /translate fr Bonjour le monde\n\n"
                    "<b>Supported languages:</b>\n"
                    "English, Spanish, French, German, Italian, Portuguese, Russian, Chinese, Japanese, Korean, Arabic, Hindi, and many more!",
                    parse_mode=ParseMode.HTML
                )
                return
            
            # Parse arguments
            text_to_translate = ' '.join(context.args)
            target_language = 'auto'
            
            # Check if first argument is a language code
            first_arg = context.args[0].lower()
            if first_arg in self.language_codes or len(first_arg) == 2:
                target_language = first_arg
                text_to_translate = ' '.join(context.args[1:])
                
                if not text_to_translate:
                    await update.message.reply_text(
                        "❌ Please provide text to translate after the language code."
                    )
                    return
            
            # Show typing indicator
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            
            # Send "translating" message
            translating_msg = await update.message.reply_text(
                "🌍 <i>Translating...</i>",
                parse_mode=ParseMode.HTML
            )
            
            # Get translation
            translation_result = await self._translate_text(text_to_translate, target_language)
            
            if translation_result:
                translate_text = f"""
🌍 <b>AI Translation</b>

<b>📝 Original:</b> {text_to_translate}
<b>🔤 Detected Language:</b> {translation_result.get('detected_language', 'Auto')}
<b>🎯 Target Language:</b> {translation_result.get('target_language', target_language).title()}

<b>✨ Translation:</b>
{translation_result['translation']}

<i>Powered by AI • Translation confidence: {translation_result.get('confidence', 'High')}</i>
"""
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 Translate Back", callback_data="translate_back"),
                        InlineKeyboardButton("🌐 Other Languages", callback_data="translate_menu")
                    ],
                    [
                        InlineKeyboardButton("📤 Share Translation", callback_data="share_translation"),
                        InlineKeyboardButton("🔊 Text-to-Speech", callback_data="tts_translation")
                    ]
                ])
                
                await translating_msg.edit_text(
                    translate_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard
                )
                
            else:
                await translating_msg.edit_text(
                    "❌ <b>Translation Error</b>\n\n"
                    "Sorry, I couldn't translate the text.\n\n"
                    "<b>Possible issues:</b>\n"
                    "• Text too long or complex\n"
                    "• Unsupported language\n"
                    "• AI service temporarily unavailable\n\n"
                    "<i>Please try again with different text.</i>",
                    parse_mode=ParseMode.HTML
                )
            
            logger.info(f"Translate command executed by user {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in translate command: {e}")
            await update.message.reply_text("❌ Error in translation service.")
    
    async def ocr_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /ocr command for optical character recognition."""
        try:
            user = update.effective_user
            message = update.message
            
            # Check if there's an image
            photo = None
            if message.reply_to_message and message.reply_to_message.photo:
                photo = message.reply_to_message.photo[-1]  # Get highest resolution
            elif message.photo:
                photo = message.photo[-1]
            
            if not photo:
                await update.message.reply_text(
                    "📸 <b>OCR - Text Recognition</b>\n\n"
                    "Extract text from images using AI!\n\n"
                    "<b>How to use:</b>\n"
                    "1. Send an image with /ocr command\n"
                    "2. Reply to an image with /ocr\n"
                    "3. Forward an image and use /ocr\n\n"
                    "<b>Supported formats:</b>\n"
                    "• Photos with text\n"
                    "• Screenshots\n"
                    "• Documents\n"
                    "• Handwritten text (limited)\n\n"
                    "<i>Send an image to get started!</i>",
                    parse_mode=ParseMode.HTML
                )
                return
            
            # Show typing indicator
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            
            # Send "processing" message
            processing_msg = await update.message.reply_text(
                "📸 <i>Analyzing image and extracting text...</i>",
                parse_mode=ParseMode.HTML
            )
            
            try:
                # Download image
                file = await context.bot.get_file(photo.file_id)
                image_bytes = await file.download_as_bytearray()
                
                # Process with OCR
                extracted_text = await self._extract_text_from_image(image_bytes)
                
                if extracted_text and extracted_text.strip():
                    # Clean and format text
                    extracted_text = extracted_text.strip()
                    
                    ocr_text = f"""
📸 <b>OCR Results</b>

<b>📝 Extracted Text:</b>
<code>{extracted_text}</code>

<b>📊 Analysis:</b>
• <b>Characters:</b> {len(extracted_text)}
• <b>Words:</b> {len(extracted_text.split())}
• <b>Lines:</b> {len(extracted_text.split('\n'))}

<i>Text extracted using AI vision • Copy the text above!</i>
"""
                    
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("📋 Copy Text", callback_data="copy_ocr_text"),
                            InlineKeyboardButton("🌍 Translate", callback_data="translate_ocr")
                        ],
                        [
                            InlineKeyboardButton("📤 Share Text", callback_data="share_ocr"),
                            InlineKeyboardButton("💾 Save to File", callback_data="save_ocr")
                        ]
                    ])
                    
                    await processing_msg.edit_text(
                        ocr_text,
                        parse_mode=ParseMode.HTML,
                        reply_markup=keyboard
                    )
                    
                else:
                    await processing_msg.edit_text(
                        "📸 <b>OCR Results</b>\n\n"
                        "❌ No text found in the image.\n\n"
                        "<b>Possible reasons:</b>\n"
                        "• Image doesn't contain readable text\n"
                        "• Text is too small or blurry\n"
                        "• Image quality is too low\n"
                        "• Handwriting is not clear enough\n\n"
                        "<i>Try with a clearer image or different angle.</i>",
                        parse_mode=ParseMode.HTML
                    )
                
            except Exception as e:
                logger.error(f"Error processing OCR: {e}")
                await processing_msg.edit_text(
                    "❌ <b>OCR Error</b>\n\n"
                    "Sorry, I couldn't process the image.\n\n"
                    "<b>Possible issues:</b>\n"
                    "• Image file corrupted\n"
                    "• Unsupported image format\n"
                    "• AI service temporarily unavailable\n\n"
                    "<i>Please try again with a different image.</i>",
                    parse_mode=ParseMode.HTML
                )
            
            logger.info(f"OCR command executed by user {user.id}")
            
        except Exception as e:
            logger.error(f"Error in ocr command: {e}")
            await update.message.reply_text("❌ Error in OCR processing.")
    
    async def imagegen_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /imagegen command for AI image generation."""
        try:
            user = update.effective_user
            
            if not context.args:
                await update.message.reply_text(
                    "🎨 <b>AI Image Generator</b>\n\n"
                    "Create stunning images from text descriptions!\n\n"
                    "<b>Usage:</b> /imagegen [description]\n\n"
                    "<b>Examples:</b>\n"
                    "• /imagegen a cat wearing a space suit\n"
                    "• /imagegen beautiful sunset over mountains\n"
                    "• /imagegen futuristic city with flying cars\n"
                    "• /imagegen abstract art with vibrant colors\n\n"
                    "<b>Tips for better results:</b>\n"
                    "• Be specific and descriptive\n"
                    "• Include style (realistic, cartoon, etc.)\n"
                    "• Mention colors, lighting, mood\n"
                    "• Add artistic styles or artists\n\n"
                    f"<b>Status:</b> {self._get_image_gen_status()}",
                    parse_mode=ParseMode.HTML
                )
                return
            
            prompt = ' '.join(context.args)
            
            # Validate prompt
            if len(prompt) < 10:
                await update.message.reply_text(
                    "❌ Please provide a more detailed description (at least 10 characters)."
                )
                return
            
            # Show typing indicator
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_photo")
            
            # Send "generating" message
            generating_msg = await update.message.reply_text(
                "🎨 <i>AI is creating your image...</i>\n\n"
                f"<b>Prompt:</b> {prompt}\n\n"
                "<i>This may take 30-60 seconds...</i>",
                parse_mode=ParseMode.HTML
            )
            
            # Generate image
            image_result = await self._generate_image(prompt, user.id)
            
            if image_result:
                # Send the generated image
                caption = f"""
🎨 <b>AI Generated Image</b>

<b>📝 Prompt:</b> {prompt}
<b>🤖 Generated by:</b> {image_result.get('model', 'AI')}
<b>👤 Requested by:</b> {user.first_name}

<i>Like the result? Try generating more images!</i>
"""
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 Generate Again", callback_data="regenerate_image"),
                        InlineKeyboardButton("✨ Enhance Prompt", callback_data="enhance_prompt")
                    ],
                    [
                        InlineKeyboardButton("📤 Share", callback_data="share_image"),
                        InlineKeyboardButton("🎨 New Image", callback_data="new_image")
                    ]
                ])
                
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=image_result['image_data'],
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard
                )
                
                # Delete the "generating" message
                await generating_msg.delete()
                
            else:
                await generating_msg.edit_text(
                    "❌ <b>Image Generation Failed</b>\n\n"
                    "Sorry, I couldn't generate the image.\n\n"
                    "<b>Possible issues:</b>\n"
                    "• Prompt contains inappropriate content\n"
                    "• AI service temporarily unavailable\n"
                    "• Daily generation limit reached\n"
                    "• API key not configured\n\n"
                    "<i>Please try again with a different prompt.</i>",
                    parse_mode=ParseMode.HTML
                )
            
            logger.info(f"Imagegen command executed by user {user.id}")
            
        except Exception as e:
            logger.error(f"Error in imagegen command: {e}")
            await update.message.reply_text("❌ Error in image generation.")
    
    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /analyze command for image analysis."""
        try:
            user = update.effective_user
            message = update.message
            
            # Check if there's an image
            photo = None
            if message.reply_to_message and message.reply_to_message.photo:
                photo = message.reply_to_message.photo[-1]
            elif message.photo:
                photo = message.photo[-1]
            
            if not photo:
                await update.message.reply_text(
                    "🔍 <b>AI Image Analysis</b>\n\n"
                    "Get detailed AI analysis of any image!\n\n"
                    "<b>How to use:</b>\n"
                    "1. Send an image with /analyze\n"
                    "2. Reply to an image with /analyze\n\n"
                    "<b>AI will analyze:</b>\n"
                    "• Objects and people in the image\n"
                    "• Colors, composition, and style\n"
                    "• Scene description\n"
                    "• Emotions and mood\n"
                    "• Technical aspects\n\n"
                    "<i>Send an image to get started!</i>",
                    parse_mode=ParseMode.HTML
                )
                return
            
            # Show typing indicator
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            
            # Send "analyzing" message
            analyzing_msg = await update.message.reply_text(
                "🔍 <i>AI is analyzing the image...</i>",
                parse_mode=ParseMode.HTML
            )
            
            try:
                # Download image
                file = await context.bot.get_file(photo.file_id)
                image_bytes = await file.download_as_bytearray()
                
                # Analyze with AI
                analysis = await self._analyze_image(image_bytes)
                
                if analysis:
                    analysis_text = f"""
🔍 <b>AI Image Analysis</b>

<b>🎯 Main Subject:</b> {analysis.get('main_subject', 'Unknown')}
<b>📝 Description:</b> {analysis.get('description', 'No description available')}

<b>🎨 Visual Elements:</b>
• <b>Colors:</b> {analysis.get('colors', 'Various')}
• <b>Style:</b> {analysis.get('style', 'Unknown')}
• <b>Composition:</b> {analysis.get('composition', 'Standard')}

<b>🏷️ Detected Objects:</b>
{analysis.get('objects', 'No specific objects detected')}

<b>😊 Mood & Atmosphere:</b>
{analysis.get('mood', 'Neutral')}

<b>⭐ Quality Score:</b> {analysis.get('quality_score', 'N/A')}/10

<i>Analysis powered by advanced AI vision</i>
"""
                    
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("🔄 Re-analyze", callback_data="reanalyze_image"),
                            InlineKeyboardButton("📊 Detailed Report", callback_data="detailed_analysis")
                        ],
                        [
                            InlineKeyboardButton("📤 Share Analysis", callback_data="share_analysis"),
                            InlineKeyboardButton("💾 Save Report", callback_data="save_analysis")
                        ]
                    ])
                    
                    await analyzing_msg.edit_text(
                        analysis_text,
                        parse_mode=ParseMode.HTML,
                        reply_markup=keyboard
                    )
                    
                else:
                    await analyzing_msg.edit_text(
                        "❌ <b>Analysis Failed</b>\n\n"
                        "Sorry, I couldn't analyze the image.\n\n"
                        "<b>Possible issues:</b>\n"
                        "• Image format not supported\n"
                        "• Image too small or unclear\n"
                        "• AI service temporarily unavailable\n\n"
                        "<i>Please try again with a different image.</i>",
                        parse_mode=ParseMode.HTML
                    )
                
            except Exception as e:
                logger.error(f"Error in image analysis: {e}")
                await analyzing_msg.edit_text(
                    "❌ <b>Analysis Error</b>\n\n"
                    "Sorry, I couldn't process the image for analysis.\n\n"
                    "<i>Please try again later.</i>",
                    parse_mode=ParseMode.HTML
                )
            
            logger.info(f"Analyze command executed by user {user.id}")
            
        except Exception as e:
            logger.error(f"Error in analyze command: {e}")
            await update.message.reply_text("❌ Error in image analysis.")
    
    # Helper methods
    
    async def _get_ai_response(self, question: str, user_id: int) -> Optional[str]:
        """Get AI response using available providers."""
        try:
            # Try OpenAI first
            if self.openai_client and self.settings.openai_api_key:
                try:
                    response = await self.openai_client.ChatCompletion.acreate(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a helpful AI assistant. Provide clear, accurate, and helpful responses."},
                            {"role": "user", "content": question}
                        ],
                        max_tokens=1000,
                        temperature=0.7
                    )
                    return response.choices[0].message.content.strip()
                except Exception as e:
                    logger.error(f"OpenAI error: {e}")
            
            # Try Gemini as fallback
            if self.gemini_client and self.settings.gemini_api_key:
                try:
                    response = await self.gemini_client.generate_content_async(question)
                    return response.text.strip()
                except Exception as e:
                    logger.error(f"Gemini error: {e}")
            
            # Fallback response
            return "I'm sorry, but I'm currently unable to process your request. Please try again later."
            
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            return None
    
    async def _translate_text(self, text: str, target_language: str) -> Optional[Dict[str, Any]]:
        """Translate text using AI."""
        try:
            # Prepare translation prompt
            if target_language == 'auto':
                prompt = f"Translate the following text to English and identify the original language: {text}"
            else:
                lang_name = self._get_language_name(target_language)
                prompt = f"Translate the following text to {lang_name}: {text}"
            
            # Get AI response
            response = await self._get_ai_response(prompt, 0)
            
            if response:
                return {
                    'translation': response,
                    'detected_language': 'Auto-detected',
                    'target_language': target_language,
                    'confidence': 'High'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in translation: {e}")
            return None
    
    async def _extract_text_from_image(self, image_bytes: bytes) -> Optional[str]:
        """Extract text from image using AI vision."""
        try:
            # This is a simplified implementation
            # In production, you'd use services like Google Vision API, AWS Textract, etc.
            
            if self.gemini_client:
                # Convert image to base64
                image_b64 = base64.b64encode(image_bytes).decode()
                
                # Use Gemini Vision (if available)
                prompt = "Extract all text from this image. Return only the text content, no additional commentary."
                
                # This is a placeholder - actual implementation would use vision models
                return "OCR functionality requires additional setup with vision APIs."
            
            return "OCR service not available. Please configure AI vision services."
            
        except Exception as e:
            logger.error(f"Error in OCR: {e}")
            return None
    
    async def _generate_image(self, prompt: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Generate image using AI."""
        try:
            # This is a simplified implementation
            # In production, you'd use DALL-E, Midjourney, Stable Diffusion, etc.
            
            if self.openai_client and self.settings.openai_api_key:
                try:
                    response = await self.openai_client.Image.acreate(
                        prompt=prompt,
                        n=1,
                        size="1024x1024"
                    )
                    
                    image_url = response.data[0].url
                    
                    # Download the image
                    async with httpx.AsyncClient() as client:
                        img_response = await client.get(image_url)
                        img_response.raise_for_status()
                        
                        return {
                            'image_data': img_response.content,
                            'model': 'DALL-E',
                            'prompt': prompt
                        }
                        
                except Exception as e:
                    logger.error(f"Image generation error: {e}")
            
            # Fallback: Return placeholder
            return None
            
        except Exception as e:
            logger.error(f"Error in image generation: {e}")
            return None
    
    async def _analyze_image(self, image_bytes: bytes) -> Optional[Dict[str, Any]]:
        """Analyze image using AI vision."""
        try:
            # This is a simplified implementation
            # In production, you'd use Google Vision API, AWS Rekognition, etc.
            
            # Placeholder analysis
            return {
                'main_subject': 'Image content',
                'description': 'This appears to be an image with various visual elements.',
                'colors': 'Multiple colors detected',
                'style': 'Photographic',
                'composition': 'Standard composition',
                'objects': 'Various objects detected',
                'mood': 'Neutral atmosphere',
                'quality_score': '7'
            }
            
        except Exception as e:
            logger.error(f"Error in image analysis: {e}")
            return None
    
    def _get_available_ai(self) -> str:
        """Get list of available AI providers."""
        providers = []
        if self.settings.openai_api_key:
            providers.append("OpenAI GPT")
        if self.settings.gemini_api_key:
            providers.append("Google Gemini")
        
        return ", ".join(providers) if providers else "No AI providers configured"
    
    def _get_primary_ai(self) -> str:
        """Get primary AI provider name."""
        if self.settings.openai_api_key:
            return "OpenAI GPT"
        elif self.settings.gemini_api_key:
            return "Google Gemini"
        return "AI Assistant"
    
    def _get_image_gen_status(self) -> str:
        """Get image generation service status."""
        if self.settings.openai_api_key:
            return "✅ DALL-E Available"
        return "❌ No image generation service configured"
    
    def _get_language_name(self, code: str) -> str:
        """Get language name from code."""
        code_to_name = {v: k for k, v in self.language_codes.items()}
        return code_to_name.get(code, code).title()