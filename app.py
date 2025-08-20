# app.py

from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import fitz
import os
import re
from collections import defaultdict
import uuid
import google.generativeai as genai
from dotenv import load_dotenv

# --- Load environment variables from .env file ---
load_dotenv()

app = FastAPI(title="Sustainability Lens MVP")

# --- Configure the Gemini API client ---
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    print("Gemini API configured successfully.")
except Exception as e:
    print(f"Error configuring Gemini API: {e}")

# --- Static Directory and CORS ---
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# --- Text Extraction Function ---
def extract_text_with_pages(file_path: str):
    doc_pages = []
    with fitz.open(file_path) as pdf:
        for page_num, page in enumerate(pdf, start=1):
            doc_pages.append((page_num, page.get_text("text").split('\n')))
    return doc_pages

# --- KEY CHANGE 1: The "Smart Filter" - A small list of high-signal keywords ---
GENERIC_ESG_KEYWORDS = [
    "GRI", "SASB", "TCFD", "CDP", "ISSB", "UNGC", "SBTi", "GHG", "SLCP", "ZDHC", 
    "FLA", "RBA", "RLI", "SEDEX", "B Corp", "RE100", "EP100", "WRI", "WBCSD",
    "UNGPs", "ILO", "SA8000", "ETI", "TNFD", "PRI", "GRESB", "MSCI",
    "sustainability", "governance", "human rights", "diversity", "inclusion", "equity",
    "emissions", "circular economy", "supply chain", "decarbonization", "net-zero",
    "climate", "environmental", "social", "labor", "ethics", "compliance"
]
KEYWORD_PATTERN = re.compile(r'\b(' + '|'.join(GENERIC_ESG_KEYWORDS) + r')\b', re.IGNORECASE)

# --- KEY CHANGE 2: A fast function to find "interesting" sentences ---
def find_candidate_sentences(doc_pages: list):
    candidate_sentences = []
    for page_num, lines in doc_pages:
        for line in lines:
            if KEYWORD_PATTERN.search(line) and len(line.strip()) > 20:
                candidate_sentences.append({ "page": page_num, "sentence": line.strip() })
    print(f"Found {len(candidate_sentences)} potentially relevant sentences.")
    return candidate_sentences

# --- KEY CHANGE 3: The powerful, single-call Gemini analysis function ---
def analyze_sentences_with_gemini(candidate_sentences: list):
    final_results = defaultdict(lambda: defaultdict(list))
    if not candidate_sentences:
        return final_results

    CATEGORIES = [
        "Key Global ESG Reporting Frameworks & Standards",
        "Key Industry-Specific & Sector Tools/Programs",
        "Key Environmental & Climate Initiatives",
        "Key Social & Governance Standards",
        "Circular Economy & Product Stewardship",
        "Financial, Investment, and Assurance Bodies"
    ]
    sentences_for_prompt = json.dumps(candidate_sentences, indent=2)

    prompt = f"""
    You are an expert ESG analyst. Your task is to analyze a pre-filtered list of sentences from a sustainability report and extract all specific ESG initiatives.

    For each piece of evidence you find, you must provide:
    1. The official name of the initiative (e.g., "Global Reporting Initiative (GRI)").
    2. The exact page number where it was found (from the JSON input).
    3. The category it belongs to from the official list below.
    4. The full sentence that serves as evidence (from the JSON input).

    Official Categories:
    {json.dumps(CATEGORIES, indent=2)}

    Analyze ONLY the following JSON list of sentences:
    --- SENTENCE LIST START ---
    {sentences_for_prompt}
    --- SENTENCE LIST END ---

    Respond ONLY with a JSON array of objects. Each object must have four keys: "initiative", "category", "page", and "evidence_sentence".
    If you find nothing in the text, respond with an empty array [].
    Do not include any other text, explanations, or markdown formatting.
    """

    try:
        print("Sending filtered sentences to Gemini API for final analysis...")
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = model.generate_content(prompt)
        
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json\n", "").replace("\n```", "")

        findings = json.loads(response_text)

        for finding in findings:
            if all(key in finding for key in ["initiative", "category", "page", "evidence_sentence"]):
                final_results[finding["category"]][finding["initiative"]].append({
                    "page": finding["page"],
                    "evidence": finding["evidence_sentence"],
                    "highlight_text": finding["initiative"]
                })
        print("Gemini API analysis complete.")
    except Exception as e:
        print(f"An unexpected error occurred during Gemini AI analysis: {e}")

    return final_results

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        unique_id = uuid.uuid4().hex
        safe_filename = f"{unique_id}_{file.filename}"
        file_location = os.path.join(UPLOAD_DIR, safe_filename)

        with open(file_location, "wb") as f:
            f.write(await file.read())

        doc_pages = extract_text_with_pages(file_location)
        
        # --- The new, fast workflow ---
        candidate_sentences = find_candidate_sentences(doc_pages)
        detected_initiatives = analyze_sentences_with_gemini(candidate_sentences)
        
        total_mentions = sum(len(mentions) for initiatives in detected_initiatives.values() for mentions in initiatives.values())
        score = min(100, total_mentions)
        grade = "A - Excellent" if score >= 80 else "B - Good" if score >= 50 else "C - Needs Improvement"
        
        file_url = f"/static/uploads/{safe_filename}"

        return {
            "Company": file.filename.replace(".pdf", ""),
            "ESG Score": score,
            "Grade": grade,
            "Detected_Initiatives": detected_initiatives,
            "AI_Summary": "", # The summary feature is removed
            "File_URL": file_url,
            "Status": "Completed ✅"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.get("/define-initiative/")
async def define_initiative(name: str):
    # This endpoint remains for the hover-to-define feature
    try:
        if not os.getenv("GOOGLE_API_KEY"):
            return {"definition": "Definition feature disabled: API key not configured."}
        print(f"Fetching definition for: {name}")
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        prompt = f"In one concise sentence, explain what the '{name}' is in the context of ESG and sustainability."
        response = model.generate_content(prompt)
        return {"definition": response.text.strip() if response.text else "Could not find a definition."}
    except Exception as e:
        print(f"Error fetching definition: {e}")
        return {"definition": "Error fetching definition."}

# Serve the frontend
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")