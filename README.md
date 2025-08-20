# Sustainability Lens: AI-Powered ESG Report Analysis

Sustainability Lens is a web-based MVP designed to help analysts rapidly analyze corporate sustainability and ESG (Environmental, Social, and Governance) reports. The tool extracts key ESG initiatives, provides interactive evidence, and uses the Google Gemini API for intelligent context.

This project was developed with a focus on balancing cutting-edge AI capabilities with real-world performance and usability.

---

### ✨ Live Demo

*[Link to your Loom/YouTube video demo here]*

---

### Key Features

*   **Hybrid AI Architecture:** Employs a "Smart Filter" pipeline. A fast, local regex scan identifies potentially relevant sentences, which are then sent in a single, optimized batch to the Google Gemini API for advanced analysis and categorization.
*   **Interactive Analyst Cockpit:** A professional two-panel UI that displays a dashboard of quantitative metrics alongside an interactive, searchable list of all detected evidence.
*   **Live Document Viewer:** A seamlessly integrated PDF viewer that automatically navigates to the precise page of any selected piece of evidence, allowing for instant verification.
*   **"Hover-to-Define" Context:** An AI-powered tooltip provides instant, concise definitions of any detected ESG acronym or initiative, turning the tool into a valuable learning platform.
*   **Advanced UI/UX:** Features include a drag-and-drop file uploader, real-time evidence search, and "Expand/Collapse All" controls for a highly efficient analysis workflow.

### 🛠️ Tech Stack

*   **Backend:** Python with **FastAPI**
*   **Frontend:** Vanilla HTML, CSS, and JavaScript (no frameworks)
*   **PDF Parsing:** PyMuPDF
*   **Primary AI Engine:** Google Gemini API (`gemini-1.5-flash-latest`)
*   **Local AI (Prototyping):** Ollama with `Llama 3 8B` and `Phi-3 Mini`

---

### A Note on Model Selection: From Local Ambition to Cloud Performance

The initial goal for this project was to create a fully self-contained analysis tool by running a powerful open-source model locally using **Ollama** with Meta's **Llama 3 8B**.

During development, it became clear that while powerful, the `Llama 3 8B` model's VRAM and processing requirements were too high for consumer-grade hardware (like systems with integrated GPUs or < 8GB of VRAM). This resulted in significant performance bottlenecks and out-of-memory errors, making the application too slow for practical use with large documents.

While a smaller model like `Phi-3 Mini` proved more stable, the "cold start" and page-by-page processing times were still not ideal for a responsive user experience.

As a result, a key product decision was made to pivot to a **hybrid cloud architecture**. This leverages the speed of a local regex scan for broad evidence filtering and the immense power and speed of the **Google Gemini API** for the final, high-quality analysis. This approach provides the best of both worlds: near-instantaneous performance for the user, regardless of their hardware, and state-of-the-art analytical intelligence.

---

### 🚀 Setup & Usage

**Prerequisites:**
*   Python 3.8+
*   A Google Gemini API Key

**1. Clone the Repository:**
```
git clone [Your-GitHub-Repo-URL]
cd [Your-Repo-Name]
```
2. Install Dependencies:
It's highly recommended to use a virtual environment.
# Create a virtual environment
```
python -m venv venv
```

# Activate it
# On Windows:
```
venv\Scripts\activate
```
# On macOS/Linux:
```
source venv/bin/activate
```

# Install the required libraries from the requirements file
```
pip install -r requirements.txt
```

3. Set Up Your API Key:
Create a file named .env in the root of the project.
Add your Google Gemini API key to this file:
```
GOOGLE_API_KEY="AIzaSy...your...long...api...key...here"
```

5. Run the Application:
Start the FastAPI server from your terminal:
```
uvicorn app:app --reload
```

Open your web browser and navigate to http://127.0.0.1:8000.

7. How to Use:
Drag and drop a PDF sustainability report onto the upload area, or click to select a file.
Click the "Analyze" button.
Explore the results in the two-panel analyst cockpit. Click on any evidence item to view it in the PDF.
Use the search bar to filter the evidence list in real-time.
Hover over the (ⓘ) icon next to any initiative to get an instant, AI-powered definition.
