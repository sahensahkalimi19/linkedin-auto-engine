import os
import json
import random
import time
import requests
from google import genai
from PIL import Image, ImageDraw, ImageFont
from linkedin_api import Linkedin

# 1. API Keys & Profile Setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINKEDIN_USERNAME = os.getenv("LINKEDIN_USERNAME")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is missing!")

# Initialize new Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

# Load profile data safely
try:
    with open("profile_data.json", "r", encoding="utf-8") as f:
        profile_info = json.load(f)
except Exception as e:
    print(f"Error loading profile_data.json: {e}")
    profile_info = {
        "name": "Usman Gani",
        "title": "AI Data Quality Analyst & Python Developer",
        "education": "BCA Data Science Student",
        "featured_projects": []
    }

# 2. Content Categories for Rotation
CATEGORIES = [
    "ML_ALGORITHM_GUIDE", 
    "AI_SKILLS_ROADMAP", 
    "PYTHON_AUTOMATION_TIP", 
    "TECH_NEWS_INSIGHT"
]
current_category = random.choice(CATEGORIES)

# 3. Fetch Gemini Post Text & Infographic Card Data (With Fallback & 503 Protection)
def generate_content(category, profile):
    prompt = f"""
    You are an expert AI & Data Science Thought Leader managing LinkedIn for {profile['name']} ({profile['title']}, {profile['education']}).
    Current Category: {category}
    
    User Profile Projects to subtly relate (if relevant):
    {json.dumps(profile.get('featured_projects', []))}
    
    Generate a high-value LinkedIn post. Structure:
    1. A short, catchy title for a visual infographic card (Max 8 words).
    2. 3 to 4 short, crisp bullet points for the visual card layout (Keep each bullet under 10-12 words).
    3. The main LinkedIn Post caption (engaging, educational, professional, with hashtags).
    
    Return output strictly in valid JSON format with double quotes, no markdown text outside JSON:
    {{
        "card_title": "...",
        "card_bullets": ["...", "...", "..."],
        "caption": "..."
    }}
    """
    
    # Fallback models list in case one experiences high traffic (503)
    models_to_try = ['gemini-3.8-flash', 'gemini-3.5-flash-lite', 'gemini-3.1-flash-lite']
    
    for model_name in models_to_try:
        for attempt in range(2):
            try:
                print(f"Trying model {model_name} (Attempt {attempt + 1})...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                
                raw_text = response.text.strip()
                # Safe JSON extraction
                if "```json" in raw_text:
                    clean_json = raw_text.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_text:
                    clean_json = raw_text.split("```")[1].split("```")[0].strip()
                else:
                    clean_json = raw_text
                    
                return json.loads(clean_json)
                
            except Exception as e:
                print(f"Model {model_name} failed on attempt {attempt + 1}: {e}")
                time.sleep(3)
                
    raise RuntimeError("All Gemini models are currently experiencing high traffic (503). Please try again later.")

# 4. Helper Function to Wrap Long Text on Image
def draw_wrapped_text(draw, text, start_x, start_y, max_width, font, fill_color, line_spacing=45):
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = font.getbbox(test_line)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
        
    y = start_y
    for line in lines:
        draw.text((start_x, y), line, fill=fill_color, font=font)
        y += line_spacing
    return y

# 5. Generate Dynamic Infographic/Visual Card
def create_visual_card(card_data):
    THEMES = [
        {"bg": "#0f172a", "text": "#ffffff", "accent": "#38bdf8"}, # Dark Slate Tech
        {"bg": "#18181b", "text": "#f4f4f5", "accent": "#22c55e"}, # Matrix Green Accent
        {"bg": "#0f2027", "text": "#ffffff", "accent": "#ff007f"}  # Cyberpunk Magenta
    ]
    theme = random.choice(THEMES)
    
    img = Image.new('RGB', (1080, 1080), color=theme["bg"])
    draw = ImageDraw.Draw(img)
    
    # Load fonts safely
    try:
        title_font = ImageFont.truetype("arial.ttf", 50)
        body_font = ImageFont.truetype("arial.ttf", 34)
        footer_font = ImageFont.truetype("arial.ttf", 26)
    except:
        title_font = body_font = footer_font = ImageFont.load_default()
        
    # Draw Title with text wrapping
    title_y = draw_wrapped_text(draw, card_data["card_title"], 80, 100, 920, title_font, theme["accent"], line_spacing=60)
    draw.line((80, title_y + 20, 1000, title_y + 20), fill=theme["accent"], width=4)
    
    # Draw Bullet Points with safety margin
    y_pos = title_y + 60
    for bullet in card_data["card_bullets"]:
        draw.text((80, y_pos), "•", fill=theme["accent"], font=body_font)
        y_pos = draw_wrapped_text(draw, bullet, 130, y_pos, 870, body_font, theme["text"], line_spacing=48)
        y_pos += 25 # Gap between bullets
        
    # Footer - Personal Branding
    edu_text = f"{profile_info.get('name', 'Usman Gani')} | {profile_info.get('education', 'BCA Data Science Student')}"
    draw.text((80, 980), edu_text, fill="#94a3b8", font=footer_font)
    
    file_name = "generated_post_card.png"
    img.save(file_name)
    return file_name

# 6. Main Execution Flow
if __name__ == "__main__":
    print("Step 1: Generating AI Content...")
    content = generate_content(current_category, profile_info)
    
    print("Step 2: Creating Infographic Visual Card...")
    card_path = create_visual_card(content)
    
    print("Step 3: Logging into LinkedIn & Publishing...")
    if not LINKEDIN_USERNAME or not LINKEDIN_PASSWORD:
        raise ValueError("LinkedIn credentials (USERNAME/PASSWORD) are missing in environment variables!")
        
    api = Linkedin(LINKEDIN_USERNAME, LINKEDIN_PASSWORD)
    
    # Post Image and Caption to Personal Profile
    api.post_share(comment=content["caption"], image_path=card_path)
    print("Successfully Published to LinkedIn Personal Profile!")
