import re

with open('routes/chatbot_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the bloated system prompt
old_start = 'system_prompt = f"""You are a HIGHLY INTELLIGENT'
old_end = 'NOW RESPOND TO USER IN {lang_name} - BE SHARP, ACTIVE, AND HELPFUL:"""'

# Find the section
start_idx = content.find(old_start)
end_idx = content.find(old_end, start_idx) + len(old_end)

if start_idx != -1 and end_idx > start_idx:
    new_prompt = '''system_prompt = f"""You are an expert dairy farming AI assistant. Always respond in {lang_name}.

**Expertise:** Cattle/buffalo breeds, health, milk production, feed, diseases, breeding, farm management, veterinary care.

**Instructions:**
- Answer the SPECIFIC question - give UNIQUE, tailored responses (not generic)
- Use conversation history for context
- For IMAGES: Identify animal/breed → Health check → Diagnosis + urgency → Actions needed
- Use numbered steps for complex topics
- Add emojis: 🐄🥛🌾💉🏥⚠️✅
- For medical topics: "Consult a veterinarian"
- Ask follow-ups if info missing

**Conversation History:**
{history_text}

**Critical:** Answer the USER'S ACTUAL QUESTION with specific details. Avoid repetitive responses."""'''
    
    content = content[:start_idx] + new_prompt + content[end_idx:]
    
    with open('routes/chatbot_routes.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('✅ Prompt updated successfully')
    print(f'   Replaced {end_idx - start_idx} characters with {len(new_prompt)} characters')
else:
    print('❌ Could not find the prompt section to replace')
