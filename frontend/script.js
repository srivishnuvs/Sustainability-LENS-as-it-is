// frontend/script.js

document.addEventListener("DOMContentLoaded", () => {
    // UI Elements
    const mainContainer = document.getElementById("main-container");
    const analysisPanel = document.getElementById("analysis-panel");
    const pdfPanel = document.getElementById("pdf-panel");
    const tooltip = document.getElementById('tooltip');
    let fileInput, uploadArea, fileNameDisplay, analyzeButton;

    let selectedFile = null;
    
    // --- Event Listeners ---
    document.addEventListener('click', (e) => {
        const uploadAreaTarget = e.target.closest('#upload-area');
        if (uploadAreaTarget) { fileInput.click(); }
        
        const analyzeBtnTarget = e.target.closest('#analyze-btn');
        if (analyzeBtnTarget) { runAnalysis(); }

        const analyzeAnotherBtn = e.target.closest('#analyze-another-btn');
        if (analyzeAnotherBtn) { resetUI(); }
        
        if (e.target.closest('#expand-all-btn')) toggleAllDetails(true);
        if (e.target.closest('#collapse-all-btn')) toggleAllDetails(false);
        if (e.target.closest('#clear-search-btn')) {
            const searchInput = document.getElementById('search-evidence');
            searchInput.value = '';
            filterEvidence('');
            e.target.closest('#clear-search-btn').style.display = 'none';
        }
        const evidenceLink = e.target.closest('a.evidence-link');
        if (evidenceLink) {
            e.preventDefault();
            const url = evidenceLink.getAttribute('href');
            updatePdfView(url);
            const currentlyActive = document.querySelector('.evidence-item.active-evidence');
            if (currentlyActive) currentlyActive.classList.remove('active-evidence');
            evidenceLink.closest('.evidence-item').classList.add('active-evidence');
        }
    });
    
    document.addEventListener('input', (e) => { if (e.target && e.target.id === 'search-evidence') { const searchTerm = e.target.value; filterEvidence(searchTerm); document.getElementById('clear-search-btn').style.display = searchTerm ? 'block' : 'none'; } });
    document.addEventListener('change', (e) => { if (e.target && e.target.id === 'pdf-upload') { handleFileSelect(e.target.files[0]); } });
    document.addEventListener('dragover', (e) => { const target = e.target.closest('#upload-area'); if(target) { e.preventDefault(); target.classList.add('dragover'); } });
    document.addEventListener('dragleave', (e) => { const target = e.target.closest('#upload-area'); if(target) target.classList.remove('dragover'); });
    document.addEventListener('drop', (e) => { const target = e.target.closest('#upload-area'); if(target) { e.preventDefault(); target.classList.remove('dragover'); handleFileSelect(e.dataTransfer.files[0]); } });

    // --- Tooltip Logic (Unchanged) ---
    let tooltipTimeout;
    document.addEventListener('mouseover', (e) => {
        const infoIcon = e.target.closest('.info-icon');
        if (infoIcon) {
            const initiativeName = infoIcon.dataset.name;
            tooltip.textContent = 'Fetching definition...';
            tooltip.style.display = 'block';
            updateTooltipPosition(e);
            clearTimeout(tooltipTimeout);
            tooltipTimeout = setTimeout(() => {
                fetch(`/define-initiative/?name=${encodeURIComponent(initiativeName)}`)
                    .then(res => res.json())
                    .then(data => { tooltip.textContent = data.definition || 'No definition found.'; });
            }, 300);
        }
    });
    document.addEventListener('mouseout', (e) => { if (e.target.closest('.info-icon')) { clearTimeout(tooltipTimeout); tooltip.style.opacity = '0'; } });
    document.addEventListener('mousemove', updateTooltipPosition);
    function updateTooltipPosition(e) {
        if (tooltip.style.opacity === '1' || tooltip.textContent === 'Fetching definition...') {
            tooltip.style.left = `${e.clientX + 15}px`;
            tooltip.style.top = `${e.clientY + 15}px`;
            tooltip.style.opacity = '1';
        }
    }

    // --- Core Functions ---
    function handleFileSelect(file) {
        if (file && file.type === 'application/pdf') {
            selectedFile = file;
            fileNameDisplay.textContent = file.name;
            analyzeButton.disabled = false;
        }
    }

    function runAnalysis() {
        if (!selectedFile) return;
        showLoader();
        mainContainer.classList.add('analysis-active'); // --- KEY: Activate cockpit view

        const formData = new FormData();
        formData.append("file", selectedFile);
        fetch("/upload-pdf/", { method: "POST", body: formData })
            .then(res => res.json())
            .then(data => {
                if (data.error) throw new Error(data.error);
                renderDashboard(data);
            })
            .catch(handleError)
            .finally(hideLoader);
    }

    function resetUI() {
        mainContainer.classList.remove('analysis-active'); // --- KEY: Deactivate cockpit view
        renderInitialState();
        selectedFile = null;
    }
    
    function updatePdfView(url) {
        const newUrl = new URL(url, window.location.origin);
        newUrl.searchParams.set('cachebust', Date.now());
        pdfPanel.innerHTML = '<div class="pdf-container" id="pdf-container"></div>';
        const pdfContainer = document.getElementById('pdf-container');
        const iframe = document.createElement('iframe');
        iframe.src = newUrl.toString();
        pdfContainer.appendChild(iframe);
    }
    
    // --- Rendering Functions ---
    function renderDashboard(data) {
        analysisPanel.innerHTML = `
            <div class="sidebar-header"><h1><i class="fa-solid fa-leaf"></i> Sustainability Lens</h1></div>
            <div id="dashboard-content">
                <header class="dashboard-header">
                    <button id="analyze-another-btn" title="Analyze Another Report"><i class="fa-solid fa-rotate-right"></i></button>
                    <h2 id="report-title"></h2>
                    <div class="summary-grid" id="summary-grid">
                        <div class="summary-card"><div id="summary-score" class="value"></div><div class="label"> Overall ESG Score</div></div>
                        <div class="summary-card"><div id="summary-mentions" class="value"></div><div class="label"> Total Mentions</div></div>
                        <div class="summary-card"><div id="summary-categories" class="value"></div><div class="label"> Categories Detected</div></div>
                    </div>
                </header>
                <div id="breakdown-output" class="breakdown-container"></div>
            </div>`;

        document.getElementById('report-title').textContent = `Analysis for: ${data.Company}`;
        const totalMentions = Object.values(data.Detected_Initiatives).flatMap(Object.values).reduce((sum, arr) => sum + arr.length, 0);
        document.getElementById('summary-score').textContent = `${data["ESG Score"]} (${data.Grade})`;
        document.getElementById('summary-mentions').textContent = totalMentions;
        document.getElementById('summary-categories').textContent = Object.keys(data.Detected_Initiatives).length;
        renderDetailedBreakdown(data);
        updatePdfView(`${data.File_URL}#page=1`);
    }

    function renderDetailedBreakdown(data) {
        const breakdownOutput = document.getElementById("breakdown-output");
        let html = `
            <div class="breakdown-header"><h3>Detailed Evidence</h3></div>
            <div class="evidence-controls">
                <div class="search-container">
                    <input type="text" id="search-evidence" placeholder="🔍 Search evidence...">
                    <button id="clear-search-btn">&times;</button>
                </div>
                <button id="expand-all-btn" class="control-btn">Expand All</button>
                <button id="collapse-all-btn" class="control-btn">Collapse All</button>
            </div>`;

        if (Object.keys(data.Detected_Initiatives).length === 0) {
            html += '<p>No specific ESG initiatives were detected in this document.</p>';
        } else {
            const sortedCategories = Object.entries(data.Detected_Initiatives).sort((a, b) => a[0].localeCompare(b[0]));
            sortedCategories.forEach(([category, initiatives]) => {
                html += `<details class="category-details" data-category="${category}"><summary class="category-summary"><i class="fa-solid fa-chevron-right icon"></i>${category}</summary><div class="initiatives-container">`;
                const sortedInitiatives = Object.entries(initiatives).sort((a, b) => b[1].length - a[1].length);
                for (const [initiative, mentions] of sortedInitiatives) {
                    for (const mention of mentions) {
                        const encodedText = encodeURIComponent(mention.highlight_text);
                        const pdfLink = `${data.File_URL}#page=${mention.page}&toolbar=0&view=FitH&text=${encodedText}`;
                        const evidenceText = mention.evidence.replace(/</g, "&lt;").replace(/>/g, "&gt;");
                        html += `<div class="evidence-item" data-text="${(initiative + ' ' + evidenceText).toLowerCase()}"><div class="initiative-title">${initiative}<i class="fa-solid fa-circle-info info-icon" data-name="${initiative}"></i></div><em class="evidence-text">${evidenceText}</em><a href="${pdfLink}" class="evidence-link">View on Page ${mention.page}</a></div>`;
                    }
                }
                html += `</div></details>`;
            });
        }
        breakdownOutput.innerHTML = html;
    }
    
    // --- Initial State Function ---
    function renderInitialState() {
        analysisPanel.innerHTML = `
            <div class="sidebar-header"><h1><i class="fa-solid fa-leaf"></i> Sustainability Lens</h1></div>
            <div class="sidebar-controls" id="sidebar-controls">
                <div id="upload-area" class="upload-area">
                    <i class="fa-solid fa-file-arrow-up"></i>
                    <p>Drag & Drop PDF Here or click to select</p>
                    <span id="file-name">No file chosen</span>
                </div>
                <input type="file" id="pdf-upload" accept=".pdf">
                <button id="analyze-btn" class="analyze-button" disabled><i class="fa-solid fa-magnifying-glass-chart"></i> Analyze</button>
            </div>`;
        
        pdfPanel.innerHTML = ''; // Ensure PDF panel is empty initially

        // Re-assign element references after creating them
        fileInput = document.getElementById("pdf-upload");
        uploadArea = document.getElementById("upload-area");
        fileNameDisplay = document.getElementById("file-name");
        analyzeButton = document.getElementById("analyze-btn");
    }

    // --- Helper Functions ---
    const showLoader = () => document.getElementById("loader-overlay").style.display = 'flex';
    const hideLoader = () => document.getElementById("loader-overlay").style.display = 'none';
    const handleError = (error) => { console.error("Error:", error); alert(`An error occurred: ${error.message}`); resetUI(); };

    function toggleAllDetails(open) {
        document.querySelectorAll('.breakdown-container .category-details').forEach(detail => detail.open = open);
    }

    function filterEvidence(searchTerm) {
        const lowerCaseSearch = searchTerm.toLowerCase();
        document.querySelectorAll('.category-details').forEach(category => {
            let categoryVisible = false;
            category.querySelectorAll('.evidence-item').forEach(item => {
                if (item.dataset.text.includes(lowerCaseSearch)) {
                    item.style.display = 'block';
                    categoryVisible = true;
                } else {
                    item.style.display = 'none';
                }
            });
            category.style.display = categoryVisible ? 'block' : 'none';
        }
    )};

    // --- Start the application ---
    renderInitialState();
});