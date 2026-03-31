const API_HOST = window.location.hostname || 'localhost';
const API_BASE_URL = `${window.location.protocol}//${API_HOST}:8000/api/v1`;
let currentTab = 'ml';
let mlModels = [];
let dlModels = [];
let modelsLoaded = false;

const RESEARCH_FALLBACK = {
    mcnemar: {
        pvalue: 0.062617,
        significant_alpha_0_05: false
    },
    auroc: {
        baseline: 0.6046,
        optimized: 0.5836,
        difference_optimized_minus_baseline: -0.0210,
        difference_bootstrap_ci_95: [-0.0452, 0.0018]
    },
    conditions: [
        { condition: 'Baseline + Original', accuracy: 0.6218, sensitivity: 0.2469, specificity: 0.8929, roc_auc: 0.6703 },
        { condition: 'Baseline + ROI', accuracy: 0.5492, sensitivity: 0.4321, specificity: 0.6339, roc_auc: 0.6046 },
        { condition: 'Optimized + Original', accuracy: 0.4767, sensitivity: 0.9444, specificity: 0.1384, roc_auc: 0.6554 },
        { condition: 'Optimized + ROI', accuracy: 0.4793, sensitivity: 0.9506, specificity: 0.1384, roc_auc: 0.5836 }
    ]
};

const FEATURES = [
    "mean_radius", "mean_texture", "mean_perimeter", "mean_area", "mean_smoothness",
    "mean_compactness", "mean_concavity", "mean_concave_points", "mean_symmetry", "mean_fractal_dimension",
    "radius_error", "texture_error", "perimeter_error", "area_error", "smoothness_error",
    "compactness_error", "concavity_error", "concave_points_error", "symmetry_error", "fractal_dimension_error",
    "worst_radius", "worst_texture", "worst_perimeter", "worst_area", "worst_smoothness",
    "worst_compactness", "worst_concavity", "worst_concave_points", "worst_symmetry", "worst_fractal_dimension"
];

const SAMPLES = {
    benign: {
        mean_radius: 13.54, mean_texture: 14.36, mean_perimeter: 87.46, mean_area: 566.3,
        mean_smoothness: 0.09779, mean_compactness: 0.08129, mean_concavity: 0.06664,
        mean_concave_points: 0.04781, mean_symmetry: 0.1885, mean_fractal_dimension: 0.05766,
        radius_error: 0.2699, texture_error: 0.7886, perimeter_error: 2.058, area_error: 23.56,
        smoothness_error: 0.008462, compactness_error: 0.0146, concavity_error: 0.02387,
        concave_points_error: 0.01315, symmetry_error: 0.0198, fractal_dimension_error: 0.0023,
        worst_radius: 15.11, worst_texture: 19.26, worst_perimeter: 99.7, worst_area: 711.2,
        worst_smoothness: 0.144, worst_compactness: 0.1773, worst_concavity: 0.239,
        worst_concave_points: 0.1288, worst_symmetry: 0.2977, worst_fractal_dimension: 0.07259
    },
    malignant: {
        mean_radius: 17.99, mean_texture: 10.38, mean_perimeter: 122.8, mean_area: 1001.0,
        mean_smoothness: 0.1184, mean_compactness: 0.2776, mean_concavity: 0.3001,
        mean_concave_points: 0.1471, mean_symmetry: 0.2419, mean_fractal_dimension: 0.07871,
        radius_error: 1.095, texture_error: 0.9053, perimeter_error: 8.589, area_error: 153.4,
        smoothness_error: 0.006399, compactness_error: 0.04904, concavity_error: 0.05373,
        concave_points_error: 0.01587, symmetry_error: 0.03003, fractal_dimension_error: 0.006193,
        worst_radius: 25.38, worst_texture: 17.33, worst_perimeter: 184.6, worst_area: 2019.0,
        worst_smoothness: 0.1622, worst_compactness: 0.6656, worst_concavity: 0.7119,
        worst_concave_points: 0.2654, worst_symmetry: 0.4601, worst_fractal_dimension: 0.1189
    }
};

document.addEventListener('DOMContentLoaded', () => {
    initForms();
    startModelPolling();
    initResearchSnapshot();
});

function normalizeResearchData(payload) {
    if (!payload || typeof payload !== 'object') return RESEARCH_FALLBACK;

    // Backend endpoint wrapper: { source, generated_from, data }
    if (payload.data && typeof payload.data === 'object') {
        return normalizeResearchData(payload.data);
    }

    // File 1 format: statistical_significance_ablation.json
    if (payload.mcnemar && payload.auroc) {
        return {
            mcnemar: payload.mcnemar,
            auroc: payload.auroc,
            conditions: RESEARCH_FALLBACK.conditions
        };
    }

    // File 2 format: phase3_statistical_analysis.json
    if (payload.statistical_tests && payload.ablation_study) {
        const ablation = payload.ablation_study.map(row => ({
            condition: row.condition
                .replace('Model + ', '+ ')
                .replace(' Images', ''),
            accuracy: row.accuracy,
            sensitivity: row.sensitivity,
            specificity: row.specificity,
            roc_auc: row.roc_auc
        }));

        return {
            mcnemar: {
                pvalue: payload.statistical_tests.mcnemar.pvalue,
                significant_alpha_0_05: payload.statistical_tests.mcnemar.significant_at_0_05
            },
            auroc: {
                baseline: payload.statistical_tests.auroc.baseline,
                optimized: payload.statistical_tests.auroc.optimized,
                difference_optimized_minus_baseline: payload.statistical_tests.auroc.difference,
                difference_bootstrap_ci_95: payload.statistical_tests.auroc.difference_bootstrap_ci_95
            },
            conditions: ablation
        };
    }

    return RESEARCH_FALLBACK;
}

function formatSigned(value, digits = 4) {
    const n = Number(value);
    if (!Number.isFinite(n)) return '--';
    return `${n >= 0 ? '+' : ''}${n.toFixed(digits)}`;
}

function renderResearchSnapshot(data) {
    const tableBody = document.getElementById('researchTableBody');
    const pValueEl = document.getElementById('mcnemarPValue');
    const badgeEl = document.getElementById('mcnemarBadge');
    const diffEl = document.getElementById('aurocDifference');
    const ciEl = document.getElementById('aurocDifferenceCi');
    const interpretationEl = document.getElementById('researchInterpretation');

    if (!tableBody || !pValueEl || !badgeEl || !diffEl || !ciEl || !interpretationEl) return;

    const pValue = Number(data?.mcnemar?.pvalue);
    const isSignificant = Boolean(data?.mcnemar?.significant_alpha_0_05);
    const aucDiff = Number(data?.auroc?.difference_optimized_minus_baseline);
    const ci = Array.isArray(data?.auroc?.difference_bootstrap_ci_95)
        ? data.auroc.difference_bootstrap_ci_95
        : null;

    pValueEl.textContent = Number.isFinite(pValue) ? pValue.toFixed(6) : '--';
    badgeEl.textContent = isSignificant ? 'Significant' : 'Not significant';
    badgeEl.className = `sig-badge ${isSignificant ? 'significant' : 'not-significant'}`;

    diffEl.textContent = formatSigned(aucDiff, 4);
    ciEl.textContent = (ci && Number.isFinite(ci[0]) && Number.isFinite(ci[1]))
        ? `[${Number(ci[0]).toFixed(4)}, ${Number(ci[1]).toFixed(4)}]`
        : '--';

    const ciCrossesZero = ci && Number.isFinite(ci[0]) && Number.isFinite(ci[1]) && ci[0] <= 0 && ci[1] >= 0;
    interpretationEl.textContent = isSignificant
        ? 'McNemar suggests a statistically significant prediction shift between baseline and optimized models.'
        : ciCrossesZero
            ? 'Current evidence indicates no robust gain: McNemar is not significant and AUROC difference CI crosses zero.'
            : 'Current evidence indicates no statistically significant class-level shift at alpha 0.05.';

    const rows = Array.isArray(data.conditions) ? data.conditions : [];
    if (!rows.length) {
        tableBody.innerHTML = '<tr><td colspan="5">No condition summary available.</td></tr>';
        return;
    }

    tableBody.innerHTML = rows.map((row) => `
        <tr>
            <td>${row.condition}</td>
            <td>${Number(row.accuracy).toFixed(4)}</td>
            <td>${Number(row.sensitivity).toFixed(4)}</td>
            <td>${Number(row.specificity).toFixed(4)}</td>
            <td>${Number(row.roc_auc).toFixed(4)}</td>
        </tr>
    `).join('');
}

async function initResearchSnapshot() {
    const dataSources = [
        `${API_BASE_URL}/research/summary/`,
        '../experiments/results/phase3_statistical_analysis.json',
        '../experiments/results/statistical_significance_ablation.json'
    ];

    for (const source of dataSources) {
        try {
            const response = await fetch(source, { cache: 'no-cache' });
            if (!response.ok) continue;
            const payload = await response.json();
            renderResearchSnapshot(normalizeResearchData(payload));
            return;
        } catch (error) {
            // Try the next source if current path is not reachable in this deployment mode.
        }
    }

    renderResearchSnapshot(RESEARCH_FALLBACK);
}

function initForms() {
    const mlForm = document.getElementById('featuresForm');
    const fusionForm = document.getElementById('fusionFeatures');
    
    FEATURES.forEach(feature => {
        const labelText = feature.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
        const mlHtml = `
            <div class="form-group">
                <label>${labelText}</label>
                <input type="number" step="any" id="f_${feature}" data-feature="${feature}" value="0">
            </div>
        `;
        const fusionHtml = `
            <div class="form-group">
                <label>${labelText}</label>
                <input type="number" step="any" id="fusion_${feature}" data-feature="${feature}" value="0">
            </div>
        `;
        mlForm.insertAdjacentHTML('beforeend', mlHtml);
        fusionForm.insertAdjacentHTML('beforeend', fusionHtml);
    });
}

function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(`btn-${tab}`).classList.add('active');
    
    document.querySelectorAll('.content-tab').forEach(t => t.style.display = 'none');
    document.getElementById(`${tab}Tab`).style.display = 'block';
    
    document.getElementById('resultContainer').style.display = 'none';
    updateModelDropdown();
}

let modelBenchmarks = {};

async function fetchModels() {
    try {
        const [mlRes, dlRes, benchRes] = await Promise.all([
            fetch(`${API_BASE_URL}/models/`),
            fetch(`${API_BASE_URL}/models/dl/`),
            fetch(`${API_BASE_URL}/models/benchmarks/`)
        ]);
        if (!mlRes.ok || !dlRes.ok || !benchRes.ok) {
            throw new Error(`API error: ${mlRes.status}/${dlRes.status}/${benchRes.status}`);
        }
        mlModels = await mlRes.json();
        dlModels = await dlRes.json();
        modelBenchmarks = await benchRes.json();
        
        updateModelDropdown();
        populateBenchmarks();
        modelsLoaded = true;
        return true;
    } catch (e) { console.error("Fetch models failed", e); }
    return false;
}

function setModelLoadingText(text) {
    const ids = ['modelSelect', 'fusionMlSelect'];
    ids.forEach((id) => {
        const select = document.getElementById(id);
        if (select) select.innerHTML = `<option value="">${text}</option>`;
    });
}

function startModelPolling() {
    let attempt = 0;
    const maxAttemptsBeforeWarning = 10;

    const poll = async () => {
        if (modelsLoaded) return;
        attempt += 1;

        const ok = await fetchModels();
        if (ok) return;

        if (attempt <= maxAttemptsBeforeWarning) {
            setModelLoadingText(`Waiting for backend... (${attempt})`);
        } else {
            setModelLoadingText('Still connecting backend API (port 8000)...');
        }

        // Keep retrying until backend is available (useful when models load slowly).
        setTimeout(poll, 2000);
    };

    poll();
}

function updateModelDropdown() {
    // 1. ML Tab Select
    const mlSelect = document.getElementById('modelSelect');
    if (mlSelect) {
        mlSelect.innerHTML = mlModels.map(m => {
            const bench = modelBenchmarks[m];
            const label = (bench && bench.is_recommended) ? `${m} (Recommend) 🌟` : m;
            return `<option value="${m}">${label}</option>`;
        }).join('');

        const recommendedMl = mlModels.find((m) => modelBenchmarks[m] && modelBenchmarks[m].is_recommended);
        if (recommendedMl) mlSelect.value = recommendedMl;
    }

    // 2. DL Tab Select (already defined in HTML but let's ensure consistency)
    const dlSelect = document.getElementById('dlModelSelect');
    if (dlSelect) {
        dlSelect.innerHTML = dlModels.map(m => {
            const label = (m === 'ResNet50') ? `${m} (Recommend) 🌟` : m;
            return `<option value="${m}">${label}</option>`;
        }).join('');

        if (dlModels.includes('ResNet50')) dlSelect.value = 'ResNet50';
    }

    // 3. Fusion Tab Selects
    const fMlSelect = document.getElementById('fusionMlSelect');
    const fDlSelect = document.getElementById('fusionDlSelect');
    if (fMlSelect) {
        fMlSelect.innerHTML = mlModels.map(m => {
            const bench = modelBenchmarks[m];
            const label = (bench && bench.is_recommended) ? `${m} (Recommend) 🌟` : m;
            return `<option value="${m}">${label}</option>`;
        }).join('');

        const recommendedFusionMl = mlModels.find((m) => modelBenchmarks[m] && modelBenchmarks[m].is_recommended);
        if (recommendedFusionMl) fMlSelect.value = recommendedFusionMl;
    }
    if (fDlSelect) {
        fDlSelect.innerHTML = dlModels.map(m => {
            const label = (m === 'ResNet50') ? `${m} (Recommend) 🌟` : m;
            return `<option value="${m}">${label}</option>`;
        }).join('');

        if (dlModels.includes('ResNet50')) fDlSelect.value = 'ResNet50';
    }
}

function updateRecommendationInfo() {
    // We are now showing recommendation inside the select box options,
    // so we hide the badge above it as per user request.
    const badge = document.getElementById('recommendation-badge');
    if (badge) badge.style.display = 'none';
}

window.toggleModelComparison = function() {
    const table = document.getElementById('comparisonTable');
    const arrow = document.querySelector('.arrow-icon-small');
    if (table.style.display === 'none') {
        table.style.display = 'block';
        arrow.style.transform = 'rotate(225deg)';
    } else {
        table.style.display = 'none';
        arrow.style.transform = 'rotate(45deg)';
    }
};

function populateBenchmarks() {
    const tbody = document.getElementById('benchmarkBody');
    const reasonDiv = document.getElementById('recommendationReason');
    tbody.innerHTML = '';
    
    let bestModel = null;

    Object.entries(modelBenchmarks).forEach(([name, data]) => {
        if (data.is_recommended) bestModel = { name, ...data };
        
        const row = `
            <tr class="${data.is_recommended ? 'best-row' : ''}">
                <td style="font-weight:600">${name}</td>
                <td>${(data.accuracy * 100).toFixed(1)}%</td>
                <td>${(data.sensitivity * 100).toFixed(1)}% ${data.sensitivity > 0.96 ? '🔥' : ''}</td>
                <td>${data.roc_auc.toFixed(3)}</td>
                <td>${data.rec_label || (data.is_recommended ? '✅ Yes' : '--')}</td>
            </tr>
        `;
        tbody.insertAdjacentHTML('beforeend', row);
    });

    if (bestModel) {
        reasonDiv.innerHTML = `<strong>💡 Tại sao chọn ${bestModel.name}?</strong><br>${bestModel.reason}`;
    }
}

function loadSampleData(type, isFusion = false) {
    const data = SAMPLES[type];
    const prefix = isFusion ? 'fusion_' : 'f_';
    for (const [key, val] of Object.entries(data)) {
        const el = document.getElementById(`${prefix}${key}`);
        if (el) el.value = val;
    }
}

function handleCsvUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        const content = e.target.result;
        const lines = content.split('\n');
        if (lines.length < 2) return;

        const headers = lines[0].split(',').map(h => h.trim().toLowerCase().replace(/ /g, '_'));
        const values = lines[1].split(',').map(v => v.trim());

        let matched = 0;
        headers.forEach((h, i) => {
            if (FEATURES.includes(h)) {
                const el = document.getElementById(`f_${h}`);
                const fusionEl = document.getElementById(`fusion_${h}`);
                if (el) el.value = values[i];
                if (fusionEl) fusionEl.value = values[i];
                matched++;
            }
        });
        
        if (matched > 0) {
            alert(`Successfully imported ${matched} clinical features from CSV.`);
        } else {
            alert("Could not find matching feature columns in CSV. Please ensure headers match Wisconsin dataset features.");
        }
    };
    reader.readAsText(file);
}

// Single Prediction (ML)
async function predictDiagnosis() {
    const data = {};
    FEATURES.forEach(f => data[f] = parseFloat(document.getElementById(`f_${f}`).value));
    
    toggleLoading('predictBtn', true);
    try {
        const res = await fetch(`${API_BASE_URL}/predict/?model_name=${document.getElementById('modelSelect').value}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await res.json();
        displayResult(result);
    } catch (e) { alert("Error: " + e.message); }
    finally { toggleLoading('predictBtn', false); }
}

// Single Prediction (DL)
let selectedFile = null;
function handleImageSelect(e) {
    const file = e.target.files[0];
    if (!file) return;
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (ev) => {
        const preview = document.getElementById('imagePreview');
        preview.src = ev.target.result;
        preview.style.display = 'block';
        document.getElementById('uploadPlaceholder').style.display = 'none';
        document.getElementById('predictImageBtn').disabled = false;
    };
    reader.readAsDataURL(file);
}

async function predictDiagnosisImage() {
    if (!selectedFile) return;
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    toggleLoading('predictImageBtn', true);
    try {
        const modelName = document.getElementById('dlModelSelect').value;
        const res = await fetch(`${API_BASE_URL}/predict/image/?model_name=${modelName}`, {
            method: 'POST',
            body: formData
        });
        const result = await res.json();
        displayResult(result);
    } catch (e) { alert("Error: " + e.message); }
    finally { toggleLoading('predictImageBtn', false); }
}

// FUSION PREDICTION
let fusionFile = null;
function handleFusionImageSelect(e) {
    const file = e.target.files[0];
    if (!file) return;
    fusionFile = file;
    const reader = new FileReader();
    reader.onload = (ev) => {
        const preview = document.getElementById('fusionImagePreview');
        preview.src = ev.target.result;
        preview.style.display = 'block';
        document.getElementById('fusionUploadPlaceholder').style.display = 'none';
    };
    reader.readAsDataURL(file);
}

async function predictFusion() {
    if (!fusionFile) { alert("Please upload an image first."); return; }
    
    const data = {};
    FEATURES.forEach(f => data[f] = parseFloat(document.getElementById(`fusion_${f}`).value));
    
    const formData = new FormData();
    formData.append('clinical_data', JSON.stringify(data));
    formData.append('image_file', fusionFile);
    formData.append('dl_model', document.getElementById('fusionDlSelect').value);
    formData.append('ml_model', document.getElementById('fusionMlSelect').value);

    toggleLoading('fusionBtn', true);
    try {
        const res = await fetch(`${API_BASE_URL}/predict/multimodal/`, {
            method: 'POST',
            body: formData
        });
        const result = await res.json();
        displayFusionResult(result);
    } catch (e) { alert("Fusion error: " + e.message); }
    finally { toggleLoading('fusionBtn', false); }
}

function displayResult(result) {
    document.getElementById('fusionResultsHeader').style.display = 'none';
    document.getElementById('singleResultTitle').style.display = 'block';
    
    const container = document.getElementById("resultContainer");
    container.style.display = "block";
    updateMainResultCard(result);
    
    const mlSection = document.getElementById("mlExplanations");
    const dlSection = document.getElementById("dlExplanations");
    mlSection.style.display = (currentTab === 'ml') ? 'block' : 'none';
    dlSection.style.display = (currentTab === 'dl') ? 'block' : 'none';
    
    if (currentTab === 'ml') populateSHAP(result.top_features);
    if (currentTab === 'dl') populateGradCAM(result.explanation_image, result);
    
    container.scrollIntoView({ behavior: 'smooth' });
}

function displayFusionResult(result) {
    document.getElementById('fusionResultsHeader').style.display = 'block';
    document.getElementById('singleResultTitle').style.display = 'none';
    
    const container = document.getElementById("resultContainer");
    container.style.display = "block";
    
    // Advice
    document.getElementById('fusionAdviceText').textContent = result.advice;
    const badge = document.getElementById('combinedDiagnosisBadge');
    badge.textContent = result.combined_diagnosis.toUpperCase();
    badge.className = `combined-badge ${result.combined_diagnosis === 'Malignant' ? 'badge-malignant' : 'badge-benign'}`;
    
    // Update main card with DL result (usually most visual)
    updateMainResultCard(result.dl_result);
    
    // Show BOTH explanations
    document.getElementById("mlExplanations").style.display = 'block';
    document.getElementById("dlExplanations").style.display = 'block';
    populateSHAP(result.ml_result.top_features);
    populateGradCAM(result.dl_result.explanation_image, result.dl_result);
    
    document.getElementById('analysisText').textContent = "Integrated multi-modal analysis performed.";
    
    container.scrollIntoView({ behavior: 'smooth' });
}

function updateMainResultCard(result) {
    const label = document.getElementById("diagnosisLabel");
    const confValue = document.getElementById("confidenceValue");
    const confBar = document.getElementById("confidenceBar");
    const resultCard = document.getElementById("resultCard");
    
    label.textContent = result.diagnosis.toUpperCase();
    const prob = (result.probability * 100).toFixed(1);
    confValue.textContent = `${prob}%`;
    confBar.style.width = `${prob}%`;
    
    const isMal = result.diagnosis === 'Malignant';
    label.className = `prediction-label ${isMal ? 'prediction-malignant' : 'prediction-benign'}`;
    confBar.style.backgroundColor = isMal ? '#ff3366' : '#00cc66';
    document.getElementById('analysisText').textContent = result.analysis_text;
}

window.toggleFeature = function(index) {
    const el = document.getElementById(`feature-details-${index}`);
    const arrow = el.previousElementSibling.querySelector('.arrow-icon');
    const isVisible = el.style.display === 'block';
    
    // Close all others
    document.querySelectorAll('.feature-details').forEach(d => d.style.display = 'none');
    document.querySelectorAll('.arrow-icon').forEach(a => a.style.transform = 'rotate(0deg)');
    
    if (!isVisible) {
        el.style.display = 'block';
        arrow.style.transform = 'rotate(180deg)';
    }
};

function populateSHAP(features) {
    const list = document.getElementById("featureImportanceList");
    list.innerHTML = '';
    if (!features) return;

    features.forEach((feat, index) => {
        const isHigh = feat.raw_value > feat.average_value;
        const diff = (((feat.raw_value - feat.average_value) / feat.average_value) * 100).toFixed(1);
        const diffText = isHigh ? `Cao hơn chuẩn ${diff}%` : `Thấp hơn chuẩn ${Math.abs(diff)}%`;
        const diffClass = isHigh ? 'diff-high' : 'diff-low';

        const html = `
            <div class="feature-item-accordion">
                <div class="feature-header" onclick="toggleFeature(${index})">
                    <div class="feature-title-row">
                        <span class="feature-name">${feat.feature}</span>
                        <span class="impact-badge ${feat.impact === 'Malignant Risk' ? 'impact-malignant' : 'impact-benign'}">
                            ${feat.impact === 'Malignant Risk' ? 'Nguy cơ' : 'An toàn'}
                        </span>
                    </div>
                    <i class="arrow-icon">▼</i>
                </div>
                <div class="feature-details" id="feature-details-${index}" style="display:none">
                    <div class="comparison-grid">
                        <div class="comp-box">
                            <span class="comp-label">Chỉ số hiện tại</span>
                            <span class="comp-val">${feat.raw_value.toFixed(4)}</span>
                        </div>
                        <div class="comp-box">
                            <span class="comp-label">Ngưỡng trung bình</span>
                            <span class="comp-val">${feat.average_value.toFixed(4)}</span>
                        </div>
                        <div class="comp-box highlight">
                            <span class="comp-label">Độ lệch</span>
                            <span class="comp-val ${diffClass}">${diffText}</span>
                        </div>
                    </div>
                    <div class="feature-analysis">
                        <p><strong>🩺 Giải thích:</strong> ${feat.description}</p>
                        <p><strong>💡 Lời khuyên bác sĩ:</strong> ${feat.advice}</p>
                    </div>
                </div>
            </div>
        `;
        list.insertAdjacentHTML('beforeend', html);
    });
}

function populateGradCAM(url, result) {
    const img = document.getElementById("gradcamImg");
    if (url) {
        img.src = url;
        img.style.display = 'block';
    } else {
        img.style.display = 'none';
    }

    // Populate AI analysis text
    const analysisBody = document.getElementById("dlAnalysisBody");
    const detailSections = document.getElementById("dlDetailSections");

    if (!result) return;

    const isMal = result.diagnosis === 'Malignant';
    const conf = (result.probability * 100).toFixed(1);
    const rawText = result.analysis_text || '';

    // Parse analysis text into structured HTML
    // Split by bullet point markers and section headers
    const lines = rawText.split('\n').filter(l => l.trim() !== '');

    let summaryLines = [];
    let findingLines = [];
    let recommendLines = [];
    let section = 'summary';

    lines.forEach(line => {
        const clean = line.trim();
        if (clean.includes('PHÂN TÍCH CHUYÊN SÂU') || clean.includes('Vùng nghi ngờ') || clean.includes('📍')) {
            section = 'findings';
        }
        if (clean.includes('LỜI KHUYÊN') || clean.includes('KHUYẾN NGHỊ') || clean.includes('LÂM SÀNG') || clean.includes('📋') || clean.includes('🩺')) {
            section = 'recommend';
        }

        if (section === 'summary') summaryLines.push(clean);
        else if (section === 'findings') findingLines.push(clean);
        else recommendLines.push(clean);
    });

    // Render summary in the main analysis card
    const statusClass = isMal ? 'dl-status-malignant' : 'dl-status-benign';
    const statusIcon = isMal ? '🚨' : '✅';
    const statusLabel = isMal ? `Phát hiện dấu hiệu ÁC TÍNH (${conf}%)` : `Không phát hiện bất thường (${conf}%)`;

    let summaryHtml = `
        <div class="dl-status-badge ${statusClass}">
            <span>${statusIcon} ${statusLabel}</span>
        </div>
        <div class="dl-summary-lines">
            ${summaryLines.map(l => {
                const text = l.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                if (l.startsWith('🚨') || l.startsWith('✅')) {
                    return `<p class="dl-summary-headline">${text}</p>`;
                }
                return `<p class="dl-summary-p">${text}</p>`;
            }).join('')}
        </div>
    `;
    analysisBody.innerHTML = summaryHtml;

    // Render findings and recommendations
    if (findingLines.length > 0 || recommendLines.length > 0) {
        const findingsList = document.getElementById("dlFindingsList");
        const recommendList = document.getElementById("dlRecommendList");

        findingsList.innerHTML = findingLines.map(l => {
            const text = l.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            if (l.startsWith('-') || l.startsWith('•') || l.match(/^\d+\./)) {
                return `<div class="dl-list-item">${text}</div>`;
            }
            return `<p class="dl-section-p">${text}</p>`;
        }).join('');

        recommendList.innerHTML = recommendLines.map(l => {
            const text = l.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            if (l.match(/^\d+\./)) {
                return `<div class="dl-list-item dl-recommend-item">${text}</div>`;
            }
            return `<p class="dl-section-p">${text}</p>`;
        }).join('');

        detailSections.style.display = 'grid';
    } else {
        detailSections.style.display = 'none';
    }
}

function toggleLoading(btnId, loading) {
    const btn = document.getElementById(btnId);
    btn.disabled = loading;
    btn.textContent = loading ? "Processing..." : btn.getAttribute('data-original-text') || btn.textContent;
    if (!btn.getAttribute('data-original-text')) btn.setAttribute('data-original-text', btn.textContent);
}
