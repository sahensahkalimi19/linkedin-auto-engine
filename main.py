import os
import json
import random
import requests
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
from linkedin_api import Linkedin

# 1. API Keys & Profile Setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINKEDIN_USERNAME = os.getenv("LINKEDIN_USERNAME")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

genai.configure(api_key=GEMINI_API_KEY)

# Load profile data
with open("profile_data.json", "r") as f:
    profile_info = json.load(f)

# 2. Content Categories for Rotation
CATEGORIES = [
    "ML_ALGORITHM_GUIDE", 
    "AI_SKILLS_ROADMAP", 
    "PYTHON_AUTOMATION_TIP", 
    "TECH_NEWS_INSIGHT"
]
current_category = random.choice(CATEGORIES)

# 3. Fetch Gemini Post Text & Infographic Card Data
def generate_content(category, profile):
    prompt = f"""
    You are an expert AI & Data Science Thought Leader managing LinkedIn for {profile['name']} ({profile['title']}, {profile['education']}).
    Current Category: {category}
    
    User Profile Projects to subtly relate (if relevant):
    {json.dumps(profile['featured_projects'])}
    
    Generate a high-value LinkedIn post. Structure:
    1. A short, catchy title for a visual infographic card (Max 8 words).
    2. 3 to 4 bullet points for the visual card layout.
    3. The main LinkedIn Post caption (engaging, educational, professional, with hashtags).
    
    Return output strictly in valid JSON format:
    {{
        "card_title": "...",
        "card_bullets": ["...", "...", "..."],
        "caption": "..."
    }}
    """
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    
    # Extract JSON string safely
    clean_json = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_json)

# 4. Generate Dynamic Infographic/Visual Card
def create_visual_card(card_data):
    # Dynamic Layout Themes
    THEMES = [
        {"bg": "#0f172a", "text": "#ffffff", "accent": "#38bdf8"}, # Dark Slate Tech
        {"bg": "#18181b", "text": "#f4f4f5", "accent": "#22c55e"}, # Matrix Green Accent
        {"bg": "#0f2027", "text": "#ffffff", "accent": "#ff007f"}  # Cyberpunk Magenta
    ]
    theme = random.choice(THEMES)
    
    img = Image.new('RGB', (1080, 1080), color=theme["bg"])
    draw = ImageDraw.Draw(img)
    
    # Load default fonts
    try:
        title_font = ImageFont.truetype("arial.ttf", 55)
        body_font = ImageFont.truetype("arial.ttf", 36)
        footer_font = ImageFont.truetype("arial.ttf", 28)
    except:
        title_font = body_font = footer_font = ImageFont.load_default()
        
    # Draw Title
    draw.text((80, 120), card_data["card_title"], fill=theme["accent"], font=title_font)
    draw.line((80, 210, 1000, 210), fill=theme["accent"], width=4)
    
    # Draw Bullet Points
    y_pos = 280
    for bullet in card_data["card_bullets"]:
        draw.text((100, y_pos), f"• {bullet}", fill=theme["text"], font=body_font)
        y_pos += 120
        
    # Footer - Personal Branding
    draw.text((80, 980), f"Usman Gani | {profile_info['education']}", fill="#94a3b8", font=footer_font)
    
    file_name = "generated_post_card.png"
    img.save(file_name)
    return file_name

# 5. Main Execution Flow
if __name__ == "__main__":
    print("Generating AI Content...")
    content = generate_content(current_category, profile_info)
    
    print("Creating Infographic Visual Card...")
    card_path = create_visual_card(content)
    
    print("Logging into LinkedIn & Publishing...")
    api = Linkedin(LINKEDIN_USERNAME, LINKEDIN_PASSWORD)
    
    # Post Image and Caption to Personal Profile
    api.post_share(comment=content["caption"], image_path=card_path)
    print("Successfully Published to LinkedIn Personal Profile!")