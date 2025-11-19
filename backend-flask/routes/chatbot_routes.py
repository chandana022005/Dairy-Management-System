from flask import Blueprint, request, jsonify, send_file
# Optional RAG retrieval (lightweight). If packages are not installed, retrieval becomes a no-op.
try:
    from .. import rag as rag_module
except Exception:
    import rag as rag_module
import google.generativeai as genai
from gtts import gTTS
import os
from dotenv import load_dotenv
import base64
from PIL import Image
import io

chatbot_bp = Blueprint("chatbot_bp", __name__)

# Load .env file
load_dotenv()

# Get Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️ WARNING: GEMINI_API_KEY not found in environment variables!")
    print(f"Current working directory: {os.getcwd()}")
    print(f".env file exists: {os.path.exists('.env')}")
    raise ValueError("GEMINI_API_KEY not found in .env file. Please check your .env file in backend-flask directory.")

print(f"✅ Gemini API key loaded successfully (length: {len(GEMINI_API_KEY)})")
genai.configure(api_key=GEMINI_API_KEY)

# Store conversation history per session
conversation_sessions = {}

# List available models to find the correct one
MODEL_NAME = None
available_models_list = []

try:
    models = genai.list_models()
    available_models_list = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
    print(f"📋 Available models with generateContent: {available_models_list}")
    
    # Try common model names in order of preference (including vision models)
    # Use gemini-2 models first as they're more capable
    preferred_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash", "models/gemini-2.5-flash", "models/gemini-2.0-flash", "models/gemini-1.5-pro", "models/gemini-1.5-flash"]
    
    # Check if any preferred model is available
    for pref_model in preferred_models:
        for avail_model in available_models_list:
            if pref_model in avail_model or avail_model.endswith(pref_model.split('/')[-1]):
                MODEL_NAME = avail_model.split('/')[-1]  # Get model name without 'models/' prefix
                print(f"✅ Found preferred model: {MODEL_NAME}")
                break
        if MODEL_NAME:
            break
    
    # If no preferred model found, use the first available
    if not MODEL_NAME and available_models_list:
        MODEL_NAME = available_models_list[0].split('/')[-1]
        print(f"✅ Using first available model: {MODEL_NAME}")
    elif not MODEL_NAME:
        MODEL_NAME = "gemini-1.5-flash"  # Final fallback (supports vision)
        print(f"⚠️ Using default fallback model: {MODEL_NAME}")
        
except Exception as e:
    print(f"⚠️ Could not list models: {e}")
    # Try common model names as fallback
    MODEL_NAME = "gemini-1.5-flash"  # Default fallback (supports vision)
    print(f"⚠️ Using default model: {MODEL_NAME}")

print(f"🤖 Using model: {MODEL_NAME}")

# Ensure static directory exists for voice files
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

def _format_history(history):
    """Format conversation history for context"""
    if not history:
        return "(This is the start of the conversation)"
    
    formatted = []
    for msg in history[-6:]:  # Last 6 messages (3 exchanges)
        formatted.append(f"{msg['role'].upper()}: {msg['content'][:200]}")
    return "\n".join(formatted)

@chatbot_bp.route("/chatbot", methods=["POST"])
def chatbot_reply():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided", "reply": "I need a message to help you. Please ask me anything about dairy management!"}), 400
            
        user_input = data.get("message", "").strip()
        language = data.get("language", "en")  # Language code: en, kn, hi, etc.
        session_id = data.get("session_id", "default")  # Session ID for conversation history
        image_data = data.get("image", None)  # Base64 encoded image
        
        if not user_input and not image_data:
            return jsonify({"error": "No message provided", "reply": "Please type or speak your question and I'll be happy to help!"}), 400

        force_language = data.get("force_language", False)
        print(f"📩 Received: {user_input[:50] if user_input else 'IMAGE ONLY'}... | Lang: {language} | Force: {force_language} | Session: {session_id} | Image: {'YES' if image_data else 'NO'}")

        # Only block truly harmful content, NOT dairy/veterinary topics
        harmful_keywords = ["suicide", "self-harm", "kill myself", "end my life", "hurt others", "illegal drugs", "weapon", "bomb"]
        
        user_input_lower = user_input.lower() if user_input else ""
        
        # Check for harmful content ONLY
        if any(keyword in user_input_lower for keyword in harmful_keywords):
            safe_response = "I cannot provide information on that topic. For dairy management help, feel free to ask about milk production, farm operations, or animal care practices."
            return jsonify({
                "reply": safe_response,
                "safety_flag": True
            })
        
        # Dairy questions are SAFE - no blocking needed
        is_health_related = False
        
        # Initialize conversation history for this session
        if session_id not in conversation_sessions:
            conversation_sessions[session_id] = []
        
        # Map language codes to names
        lang_names = {
            "en": "English",
            "kn": "Kannada (ಕನ್ನಡ)",
            "hi": "Hindi (हिंदी)",
            "te": "Telugu (తెలుగు)",
            "ta": "Tamil (தமிழ்)",
            "mr": "Marathi (मराठी)"
        }
        lang_name = lang_names.get(language, "English")
        force_language = data.get("force_language", False)
        
        print(f"🌐 Language processing: {language} ({lang_name}) | Force: {force_language}")
        
        # Check if frontend is forcing language (non-English)
        language_enforcement = ""
        if force_language and language != "en":
            language_enforcement = f"\n\n🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT 🚨🚨🚨\n" \
                                  f"YOU ARE ABSOLUTELY FORBIDDEN FROM USING ENGLISH.\n" \
                                  f"EVERY SINGLE WORD MUST BE IN {lang_name}.\n" \
                                  f"USE ONLY {lang_name} NATIVE SCRIPT.\n" \
                                  f"IF YOU USE ANY ENGLISH WORDS, YOU HAVE FAILED.\n" \
                                  f"THIS IS A STRICT, NON-NEGOTIABLE RULE."
        
        # Format conversation history
        history_text = _format_history(conversation_sessions[session_id])
        
        # Build context-aware instructions based on conversation history
        history_context = ""
        if len(conversation_sessions[session_id]) > 0:
            history_context = f"""
**CONVERSATION HISTORY:**
{history_text}

**CRITICAL:** This is a FOLLOW-UP question in an ongoing conversation. 
- Build upon previous context
- Provide NEW information, NOT repetition
- If user asks for "more details", expand with DIFFERENT aspects not covered before
- Reference previous discussion only to connect new information"""
        
        # If non-English, prepend language requirement to user input too
        if force_language and language != "en":
            user_input = f"""CRITICAL INSTRUCTION: You must respond EXCLUSIVELY in {lang_name} language using {lang_name} script.
DO NOT use English. DO NOT mix languages. ONLY {lang_name}.

User's question:
{user_input}"""
        
        # Concise prompt - focuses on answering the SPECIFIC question asked
        if language != "en":
            system_prompt = f"""You are a dairy farming AI assistant.

ABSOLUTE RULE: Respond ONLY in {lang_name}. Zero English words allowed. Use {lang_name} script exclusively.

**Expertise:** Cattle breeds, health, milk production, diseases, breeding, farm management.
**Style:** Concise, direct answers.

{history_context}

**Critical Instructions:**
- Answer the SPECIFIC question asked
- Provide NEW information, not repetition
- Use numbered steps for complex topics"""
        else:
            system_prompt = f"""You are a dairy farming AI assistant. Respond in English.

**Expertise:** Cattle breeds, health, milk production, diseases, breeding, farm management.
**Style:** Concise, direct answers.

{history_context}

**Critical Instructions:**
- Answer the SPECIFIC question asked
- Provide NEW information, not repetition
- For IMAGE uploads: Identify animal, assess condition, diagnose issues, suggest actions"""

        # No blocking - answer everything related to dairy farming

        # Process image if provided
        image_content = None
        if image_data:
            try:
                # Remove data URL prefix if present
                if "base64," in image_data:
                    image_data = image_data.split("base64,")[1]
                
                # Decode base64 image
                image_bytes = base64.b64decode(image_data)
                image_content = {
                    'mime_type': 'image/jpeg',
                    'data': image_bytes
                }
                print(f"🖼️ Image decoded successfully: {len(image_bytes)} bytes")
                
                # Add image analysis prompt
                if user_input:
                    user_input = f"[User attached an image]\n{user_input}\n\nPlease analyze the image and answer the question."
                else:
                    user_input = "Please analyze this image of the animal and provide detailed observations about its health, breed, condition, and any visible issues or concerns."
                    
            except Exception as img_error:
                print(f"❌ Image decode error: {img_error}")
                image_content = None
        
        # Call Gemini API with enhanced safety settings
        model = genai.GenerativeModel(MODEL_NAME)
        
        # Configure generation for sharp, intelligent responses
        generation_config = {
            "temperature": 0.6,  # balanced creativity (avoid hallucination)
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 1800,  # allow longer detailed responses
        }
        
        # Relaxed safety - allow veterinary/medical dairy content
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
        ]
        
        # Retrieve supporting docs (RAG) if available and add as context
        retrieved = []
        try:
            retrieved = rag_module.retrieve(user_input, k=3) if hasattr(rag_module, 'retrieve') else []
        except Exception as e:
            print(f"⚠️ RAG retrieval failed: {e}")

        context_block = ""
        if retrieved:
            context_block = "\n\n---\nRelevant documents for context:\n" + "\n---\n".join([f"- {d[:500]}" for d in retrieved]) + "\n\n"

        # Generate response with context awareness - emphasize user's specific question
        if context_block:
            full_prompt = f"{system_prompt}\n\n**Reference Documents:**\n{context_block}\n\n**User Question:** {user_input}\n\n**Your Response (in {lang_name}):**"
        else:
            full_prompt = f"{system_prompt}\n\n**User Question:** {user_input}\n\n**Your Response (in {lang_name}):**"
        
        try:
            # Prepare content for API
            if image_content:
                # Use vision model with image
                contents = [image_content, full_prompt]
                print("🖼️ Generating response with image analysis...")
            else:
                # Text only
                contents = full_prompt
            
            response = model.generate_content(
                contents,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Check if response was blocked
            if response and hasattr(response, 'text') and response.text and len(response.text.strip()) > 0:
                bot_text = response.text
            elif response and hasattr(response, 'prompt_feedback'):
                print(f"⚠️ Response blocked - prompt feedback: {response.prompt_feedback}")
                bot_text = f"As a dairy expert, I can help with that! Could you provide more specific details about your situation? This will help me give you the most accurate advice."
            else:
                print(f"⚠️ Empty response received")
                bot_text = f"I'm your dairy farming expert! Please rephrase your question and I'll help with specific advice about milk production, animal health, feed, diseases, or any dairy topic. Ask me anything!"
                
        except Exception as gen_error:
            # Handle generation errors gracefully
            print(f"❌ Generation error: {gen_error}")
            print(f"❌ Full error details: {type(gen_error).__name__}: {str(gen_error)}")
            error_msg = str(gen_error).lower()
            
            if "quota" in error_msg or "rate" in error_msg or "429" in error_msg:
                # Rate limit exceeded - provide helpful fallback with actual answer
                bot_text = f"I'm experiencing high demand right now 🕐. Here's a quick answer:\n\nTo increase milk yield:\n\n1. **Nutrition** 🌾: Provide balanced feed with 16-18% protein, minerals\n2. **Water** 💧: 60-80 liters/cow/day\n3. **Comfort** 🛏️: Clean, dry bedding, proper ventilation\n4. **Health** 💉: Regular vet checks, vaccinations\n5. **Milking** 🥛: 2-3 times daily, gentle handling\n\nPlease try again in a minute for detailed advice!"
            elif "block" in error_msg or "safety" in error_msg:
                # Content was blocked - answer it anyway for dairy topics
                bot_text = f"As a dairy expert, I can help with that! Could you provide more specific details about your situation (number of animals, symptoms, current practices)? This will help me give you the most accurate advice."
            else:
                bot_text = f"I'm here to help with dairy farming! Please ask about: milk production 🥛, animal diseases 🏥, feed nutrition 🌾, breeding 🐄, or farm management 📊. What would you like to know?"
        
        # Ensure response is never empty
        if not bot_text or len(bot_text.strip()) == 0:
            bot_text = "I'm your dairy management assistant! I can help you with milk production, farm operations, animal care, business management, and more. What would you like to know?"
        
        # Truncate if too long
        if len(bot_text) > 2000:
            bot_text = bot_text[:2000] + "... Would you like me to continue with more details?"
        
        # Save to conversation history
        conversation_sessions[session_id].append({"role": "user", "content": user_input})
        conversation_sessions[session_id].append({"role": "assistant", "content": bot_text})
        
        # Keep only last 20 messages (10 exchanges)
        if len(conversation_sessions[session_id]) > 20:
            conversation_sessions[session_id] = conversation_sessions[session_id][-20:]
        
        print(f"✅ Bot reply generated: {len(bot_text)} characters | History: {len(conversation_sessions[session_id])} messages")

        # Convert text to speech with language support. Save voice file under static and return a URL reachable from client.
        voice_filename = f"voice_response_{session_id}.mp3"
        voice_path = None
        try:
            voice_path = os.path.join(STATIC_DIR, voice_filename)

            # Normalize language code (support 'kn-IN' -> 'kn') for gTTS
            lang_short = language.split('-')[0] if isinstance(language, str) and '-' in language else language
            tts_lang = lang_short if lang_short in ["en", "hi", "te", "ta", "mr", "kn"] else "en"

            tts = gTTS(text=bot_text, lang=tts_lang, slow=False)
            tts.save(voice_path)
            print(f"🔊 Voice file saved: {voice_path} (Language: {tts_lang})")
        except Exception as tts_error:
            print(f"⚠️ TTS error (continuing without voice): {tts_error}")
            voice_path = None

        # Build a host-aware voice URL so mobile clients can reach it (don't hardcode 127.0.0.1)
        voice_url = None
        try:
            if voice_path and os.path.exists(voice_path):
                base = request.host_url.rstrip('/')
                voice_url = f"{base}/chat/voice/{voice_filename}"
        except Exception as e:
            print(f"⚠️ Could not build voice_url: {e}")

        return jsonify({
            "reply": bot_text,
            "voice_url": voice_url,
            "language": language,
            "session_id": session_id,
            "conversation_length": len(conversation_sessions[session_id]),
            "safety_checked": True
        })

    except Exception as e:
        error_msg = str(e)
        print(f"Chatbot error: {error_msg}")
        
        # Always return a helpful response, even on error
        fallback_response = "I'm having trouble processing that right now, but I'm here to help! Please ask me about dairy farm management, milk production, animal care, or farm business operations. I'll do my best to assist you!"
        
        # Provide more specific error messages
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            return jsonify({
                "error": "API configuration issue",
                "reply": fallback_response
            }), 200  # Return 200 so frontend gets the fallback message
        elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
            return jsonify({
                "error": "Service temporarily unavailable",
                "reply": "I've reached my temporary limit. Please try again in a moment, and I'll be happy to help with your dairy management questions!"
            }), 200
        else:
            return jsonify({
                "error": "Processing error",
                "reply": fallback_response
            }), 200

# Route to serve voice files
@chatbot_bp.route("/voice/<filename>", methods=["GET"])
def get_voice(filename):
    try:
        voice_path = os.path.join(STATIC_DIR, filename)
        if os.path.exists(voice_path):
            return send_file(voice_path, mimetype="audio/mpeg")
        else:
            return jsonify({"error": "Voice file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Test endpoint to verify API key and list available models
@chatbot_bp.route("/test", methods=["GET"])
def test():
    try:
        models = genai.list_models()
        all_models = [{"name": m.name, "methods": list(m.supported_generation_methods)} for m in models]
        available_for_generate = [m["name"] for m in all_models if 'generateContent' in m["methods"]]
        
        return jsonify({
            "status": "OK",
            "api_key_loaded": bool(GEMINI_API_KEY),
            "api_key_length": len(GEMINI_API_KEY) if GEMINI_API_KEY else 0,
            "service": "Google Gemini",
            "current_model": MODEL_NAME,
            "available_models": available_for_generate,
            "all_models": all_models
        })
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "api_key_loaded": bool(GEMINI_API_KEY),
            "api_key_length": len(GEMINI_API_KEY) if GEMINI_API_KEY else 0,
            "service": "Google Gemini",
            "current_model": MODEL_NAME,
            "error": str(e)
        })

# Endpoint to list all available models
@chatbot_bp.route("/models", methods=["GET"])
def list_models():
    try:
        models = genai.list_models()
        result = []
        for m in models:
            result.append({
                "name": m.name,
                "display_name": m.display_name,
                "description": m.description,
                "supported_methods": list(m.supported_generation_methods)
            })
        return jsonify({
            "status": "OK",
            "models": result,
            "current_model": MODEL_NAME
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Speech-to-Text endpoint using Gemini
@chatbot_bp.route("/speech-to-text", methods=["POST"])
def speech_to_text():
    try:
        data = request.get_json()
        audio_base64 = data.get("audio")
        language = data.get("language", "en")
        
        if not audio_base64:
            return jsonify({"error": "No audio provided"}), 400
        
        print(f"🎤 Received audio for transcription, language: {language}")
        
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_base64)
        
        # Map language codes to full names for better transcription
        lang_map = {
            "en": "English",
            "kn": "Kannada",
            "hi": "Hindi",
            "te": "Telugu",
            "ta": "Tamil",
            "mr": "Marathi"
        }
        lang_name = lang_map.get(language, "English")
        
        # Use Gemini to transcribe audio
        # Note: Gemini supports audio input for transcription
        model = genai.GenerativeModel(MODEL_NAME)
        
        prompt = f"""Transcribe this audio to text. The speaker is speaking in {lang_name}. 
        Output only the transcribed text without any additional commentary or explanation.
        If the audio is in {lang_name}, provide transcription in {lang_name} script."""
        
        # Upload audio file for Gemini
        audio_file = genai.upload_file(
            path=io.BytesIO(audio_bytes),
            mime_type="audio/mpeg"
        )
        
        response = model.generate_content([prompt, audio_file])
        transcribed_text = response.text.strip()
        
        print(f"✅ Transcribed: {transcribed_text}")
        
        return jsonify({
            "text": transcribed_text,
            "language": language
        })
        
    except Exception as e:
        print(f"❌ Speech-to-text error: {e}")
        return jsonify({"error": str(e), "text": ""}), 500
