// dashboard.js 파일의 내용 전체를 아래 코드로 교체합니다.

let currentResults = []; // 분석 결과를 저장할 전역 변수

document.addEventListener('DOMContentLoaded', function() {
    initializeTabSystem();
    initializeFormHandlers();
    setupDownloadButtons();
    // 초기에는 다운로드 버튼 비활성화
    document.querySelectorAll('.download-results-btn').forEach(btn => btn.disabled = true);
});

function initializeTabSystem() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanels = document.querySelectorAll('.tab-panel');
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            if (button.disabled) return;
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanels.forEach(panel => panel.classList.remove('active'));
            button.classList.add('active');
            document.getElementById(button.getAttribute('data-tab')).classList.add('active');
        });
    });
}

function initializeFormHandlers() {
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) uploadForm.addEventListener('submit', handleVcfUpload);
    
    const filterForm = document.getElementById('filter-form');
    if (filterForm) filterForm.addEventListener('submit', handleFilterSubmit);

    // Range sliders
    document.querySelectorAll('input[type="range"]').forEach(slider => {
        const output = document.getElementById(slider.getAttribute('data-output'));
        if (output) {
            slider.addEventListener('input', () => output.textContent = slider.value);
            output.textContent = slider.value;
        }
    });
}

function handleVcfUpload(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const loadingIndicator = document.getElementById('upload-loading');
    const resultContainer = document.getElementById('upload-result');
    
    loadingIndicator.style.display = 'block';
    resultContainer.innerHTML = '';
    
    fetch('/api/upload-vcf', { method: 'POST', body: formData })
    .then(response => response.json())
    .then(data => {
        loadingIndicator.style.display = 'none';
        if (data.success) {
            resultContainer.innerHTML = `<div class="alert alert-success"><p>${data.message}</p><p>Detected ${data.variants_count} variants.</p></div>`;
            if (data.session_id) document.getElementById('session-id').value = data.session_id;
            enableAnalysisTab();
        } else {
            showError(data.message || 'File upload failed.');
        }
    })
    .catch(error => {
        loadingIndicator.style.display = 'none';
        showError(error.message);
    });
}

function enableAnalysisTab() {
    const analysisTabButton = document.querySelector('[data-tab="analysis-panel"]');
    if (analysisTabButton) {
        analysisTabButton.disabled = false;
        analysisTabButton.click();
    }
}

function handleFilterSubmit(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const loadingIndicator = document.getElementById('analysis-loading');
    
    loadingIndicator.style.display = 'block';
    ['results-table-container', 'manhattan-plot', 'odds-ratio-chart', 'ethnicity-chart'].forEach(id => {
        const el = document.getElementById(id);
        if(el) el.innerHTML = '';
    });
    
    fetch('/api/analyze', { method: 'POST', body: formData })
    .then(response => {
        if (!response.ok) {
            // 서버가 4xx, 5xx 에러를 반환했을 때 응답 내용을 보기 위함
            return response.json().then(errData => {
                throw new Error(errData.message || `Network response was not ok: ${response.statusText}`);
            });
        }
        return response.json();
    })
    .then(data => {
        loadingIndicator.style.display = 'none';
        if (data.success && data.results) {
            currentResults = data.results;
            updateVisualizations(currentResults);
            updateResultsTable(currentResults);
            document.querySelectorAll('.download-results-btn').forEach(btn => btn.disabled = false);
        } else {
            showError(data.message || "Analysis failed or returned no results.");
            currentResults = [];
            document.querySelectorAll('.download-results-btn').forEach(btn => btn.disabled = true);
        }
    })
    .catch(error => {
        loadingIndicator.style.display = 'none';
        showError(error.message);
        currentResults = [];
        document.querySelectorAll('.download-results-btn').forEach(btn => btn.disabled = true);
    });
}

function updateVisualizations(results) {
    createManhattanPlot(results);
    createOddsRatioChart(results);
    createEthnicityChart(results);
}

function createManhattanPlot(results) {
    const container = document.getElementById('manhattan-plot');
    if (!results || results.length === 0) return;
    
    const chromosomeGroups = {};
    results.forEach(variant => {
        const chrom = variant['Chromosome'] || 'undefined';
        if (!chromosomeGroups[chrom]) chromosomeGroups[chrom] = [];
        chromosomeGroups[chrom].push(variant);
    });
    
    const data = [];
    const chromosomes = Object.keys(chromosomeGroups).sort((a, b) => {
        const numA = parseInt(a.replace('chr', ''));
        const numB = parseInt(b.replace('chr', ''));
        if (!isNaN(numA) && !isNaN(numB)) return numA - numB;
        return a.localeCompare(b);
    });
    
    const colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'];
    
    chromosomes.forEach((chrom, i) => {
        const variants = chromosomeGroups[chrom];
        data.push({
            x: variants.map(v => v['Position']),
            y: variants.map(v => -Math.log10(v['P-Value'])),
            mode: 'markers', type: 'scatter', name: `Chr ${chrom}`,
            text: variants.map(v => `${v['SNP ID (rsID)']}<br>p-value: ${v['P-Value']}<br>OR: ${v['Odds Ratio / Beta']}`),
            hoverinfo: 'text', marker: { size: 6, color: colors[i % colors.length] }
        });
    });
    
    Plotly.newPlot(container, data, { title: 'Manhattan Plot', xaxis: { title: 'Chromosome Position' }, yaxis: { title: '-log10(p-value)' }, showlegend: true });
}

function createOddsRatioChart(results) {
    const container = document.getElementById('odds-ratio-chart');
    if (!results || results.length === 0) return;

    const topVariants = [...results]
        .filter(v => v['Odds Ratio / Beta'] !== null && !isNaN(v['Odds Ratio / Beta']))
        .sort((a, b) => b['Odds Ratio / Beta'] - a['Odds Ratio / Beta'])
        .slice(0, 20);

    if (topVariants.length === 0) {
        container.innerHTML = '<p>No variants with valid Odds Ratio found.</p>';
        return;
    }
        
    Plotly.newPlot(container, [{
        x: topVariants.map(v => v['SNP ID (rsID)']),
        y: topVariants.map(v => v['Odds Ratio / Beta']),
        type: 'bar', text: topVariants.map(v => `p-value: ${v['P-Value']}`), hoverinfo: 'x+y+text'
    }], { title: 'Top 20 SNPs by Odds Ratio / Beta', xaxis: { title: 'SNP ID', tickangle: -45 }, yaxis: { title: 'Odds Ratio / Beta' } });
}

function createEthnicityChart(results) {
    const container = document.getElementById('ethnicity-chart');
    if (!results || results.length === 0) return;

    const ethnicityCounts = {};
    results.forEach(variant => {
        const ethnicity = variant['Ancestry'] || 'Unknown';
        ethnicityCounts[ethnicity] = (ethnicityCounts[ethnicity] || 0) + 1;
    });
    
    Plotly.newPlot(container, [{
        values: Object.values(ethnicityCounts), labels: Object.keys(ethnicityCounts),
        type: 'pie', textinfo: 'label+percent', insidetextorientation: 'radial'
    }], { title: 'Ancestry Distribution' });
}

function updateResultsTable(results) {

    // =================================================================
    // =========== 이 코드를 함수 맨 위에 추가해 주세요 ===========
    console.log("백엔드에서 받은 데이터 원본 전체:", results);
    // =================================================================
    // =================================================================

    
    const tableContainer = document.getElementById('results-table-container');
    tableContainer.innerHTML = '';
    if (!results || results.length === 0) {
        tableContainer.innerHTML = '<p>No matching variants found.</p>';
        return;
    }
    const table = document.createElement('table');
    table.className = 'results-table';
    const thead = table.createTHead();
    const headerRow = thead.insertRow();
    const headers = [
        'SNP ID (rsID)', 
        'Associated Trait',
        'Odds Ratio / Beta',
        'P-Value',
        'Chromosome',
        'Position',
        'REF Allele',
        'Risk Allele',
        'Ancestry',
        'PubMed ID'
    ];

    // ========== 디버깅을 위해 이 줄을 추가합니다 ================
    // ====================================================
    console.log("Headers received by frontend:", headers);
    // ====================================================
    // ====================================================
        
    headers.forEach(headerText => {
        const th = document.createElement('th');
        th.textContent = headerText;
        headerRow.appendChild(th);
    });
    const tbody = table.createTBody();
    results.forEach(variantData => {
        const row = tbody.insertRow();
        
        // 정의된 헤더 순서대로 셀을 만듭니다.
        headers.forEach(header => {
            const cell = row.insertCell();
            const cellValue = variantData[header];

            // PubMed ID와 SNP ID를 링크로 만들어 줍니다.
            if (header === 'PubMed ID' && cellValue) {
                const link = document.createElement('a');
                link.href = `https://pubmed.ncbi.nlm.nih.gov/${cellValue}`;
                link.target = '_blank';
                link.textContent = cellValue;
                cell.appendChild(link);
            } else if (header === 'SNP ID (rsID)' && cellValue && String(cellValue).startsWith('rs')) {
                const link = document.createElement('a');
                link.href = `https://www.ncbi.nlm.nih.gov/snp/${cellValue}`;
                link.target = '_blank';
                link.textContent = cellValue;
                cell.appendChild(link);
            } else {
                cell.textContent = cellValue !== null && cellValue !== undefined ? cellValue : '-';
            }
        });
    });

    tableContainer.appendChild(table);
}

function setupDownloadButtons() {
    document.getElementById('download-tsv-btn').addEventListener('click', () => downloadResults('tsv'));
    document.getElementById('download-json-btn').addEventListener('click', () => downloadResults('json'));
}

function downloadResults(format) {
    if (currentResults.length === 0) {
        alert("No results to download.");
        return;
    }
    const headers = Object.keys(currentResults[0]);
    let dataStr;
    const filename = `gwas_results.${format}`;
    let mimeType;

    if (format === 'json') {
        dataStr = JSON.stringify(currentResults, null, 2);
        mimeType = 'application/json';
    } else { // tsv
        const header_str = headers.join('\t');
        const rows = currentResults.map(row => headers.map(header => row[header] === null || row[header] === undefined ? '' : row[header]).join('\t'));
        dataStr = [header_str, ...rows].join('\n');
        mimeType = 'text/tab-separated-values;charset=utf-8;';
    }
    const blob = new Blob([dataStr], { type: mimeType });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function showError(message) {
    const errorContainer = document.getElementById('error-container');
    if (errorContainer) {
        errorContainer.innerHTML = `<div class="alert alert-error"><p>Error: ${message}</p></div>`;
        errorContainer.style.display = 'block';
        setTimeout(() => { errorContainer.style.display = 'none'; }, 5000);
    } else {
        alert("Error: " + message);
    }
}