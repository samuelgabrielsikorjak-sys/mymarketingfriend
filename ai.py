# AI usage: Integration code (API calls, response parsing) written by the author, with Claude consulted to explain the Anthropic SDK and debug errors.
# The system prompts below are core application functionality (the app's product feature is using Claude to score leads and draft
# cold emails), not AI-assisted coding — see the comments directly above each system_prompt for details.
from anthropic import Anthropic
from dotenv import load_dotenv
from database import get_db
import os
import json
load_dotenv()

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))



def score_lead(name, company, sector, notes):
    conn = get_db()
    db = conn.execute("SELECT icp_desc, product_desc FROM settings LIMIT 1").fetchone()
    icp_text = db["icp_desc"]
    product_text = db["product_desc"]
    # AI usage note: this prompt is the app's core feature (Claude API call to score a lead against the user's ICP),
    # not assistance in writing the surrounding code.
    system_prompt = f"""You are a professional B2B leads manager. Evaluate this lead by comparing it to the following ICP: {icp_text}.
        Knowing product you are offering: {product_text} Score the lead from 1 to 5, where 5 is an excellent fit and 1 is a poor fit.
        Base your reasoning on concrete details from the lead's notes, sector, and company — not generic statements.
        Return strictly JSON format: {{"score": int, "score_reasoning": string}} and nothing else, no additional text."""

    user_message = f"Lead details — Name: {name}, Company: {company}, Sector: {sector}, Notes: {notes}"

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )

    
    
    raw_text = response.content[0].text
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
            
    data = json.loads(raw_text)
    return data["score"], data["score_reasoning"]

def generate_copy(name, company, sector, notes, score_reasoning, web_site_url):
    with open("scripts.txt", "r", encoding = "utf-8") as f:
        scripts_library = f.read()
    db = get_db()
    product = db.execute("SELECT product_desc FROM settings").fetchone()
    user_message = "Generate cold emails based on th information provided."

    # AI usage note: this prompt is the app's core feature (Claude API call to draft cold emails for a lead),
    # not assistance in writing the surrounding code.
    system_prompt = f"""You are a profesional cold email writer for first cold contact with lead. Use scripts:{scripts_library},
    name od person to be contacted {name}, company{company}, sector{sector}, notes{notes}, score reasoning{score_reasoning}, wee site{web_site_url} to 
    fill in blanks in script template you choose. Choose script which best performs for this specific lead. Before writing anything
    make your own research and try to verify information on make mails more juice more in touch with date/events. Always adjust available scripts to product 
    offered:{product["product_desc"]} Then write and return two cold email templates. Return strictly just JSON Return strictly just JSON {{"script_1": {{"name": "...", "email": "..."}}, ...}}
    and nothing else.Do not include any text before or after the JSON. Do not add notes, explanations, disclaimers, or commentary. Your entire response must be valid JSON and nothing else."""
    
    emails = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )
    
    raw_text = emails.content[0].text
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    raw_text = raw_text.strip()
    print("CLEANED:", raw_text)
    
    data = json.loads(raw_text)
    return data["script_1"], data["script_2"]
