document.addEventListener('DOMContentLoaded', () => {
    const sinceDateInput = document.getElementById('since-date');
    const untilDateInput = document.getElementById('until-date');
    const providerFilter = document.getElementById('provider-filter');
    const modelFilter = document.getElementById('model-filter');
    const refreshBtn = document.getElementById('refresh-btn');
    const loadingOverlay = document.getElementById('loading-overlay');
    const errorDisplay = document.getElementById('error-display');

    const inputTokensGrid = document.getElementById('input-tokens-grid');
    const outputTokensGrid = document.getElementById('output-tokens-grid');
    const elapsedTimeGrid = document.getElementById('elapsed-time-grid');

    let providersData = {};
    let usageData = [];

    // Initialize dates
    const now = new Date();
    const twentyFourHoursAgo = new Date(now.getTime() - (24 * 60 * 60 * 1000));
    
    // Format for datetime-local: YYYY-MM-DDTHH:mm
    const formatDateTime = (date) => {
        const offset = date.getTimezoneOffset() * 60000;
        const localISOTime = (new Date(date - offset)).toISOString().slice(0, 16);
        return localISOTime;
    };

    sinceDateInput.value = formatDateTime(twentyFourHoursAgo);
    untilDateInput.value = formatDateTime(now);

    // Fetch Providers
    async function fetchProviders() {
        try {
            const response = await fetch('/api/v1/providers');
            if (!response.ok) throw new Error('Failed to fetch providers');
            providersData = await response.json();
            populateProviderFilter();
        } catch (err) {
            showError(`Error fetching providers: ${err.message}`);
        }
    }

    function populateProviderFilter() {
        providerFilter.innerHTML = '<option value="all">All Providers</option>';
        Object.keys(providersData).sort().forEach(slug => {
            const option = document.createElement('option');
            option.value = slug;
            option.textContent = slug;
            providerFilter.appendChild(option);
        });
    }

    providerFilter.addEventListener('change', () => {
        populateModelFilter();
    });

    function populateModelFilter() {
        modelFilter.innerHTML = '<option value="all">All Models</option>';
        const selectedProvider = providerFilter.value;

        if (selectedProvider === 'all') {
            // If all providers, we might want to show all models from all providers
            // or just a flat list. Let's get all unique models.
            const allModels = new Set();
            Object.values(providersData).forEach(p => {
                Object.keys(p.models || {}).forEach(m => allModels.add(m));
            });
            Array.from(allModels).sort().forEach(modelId => {
                const option = document.createElement('option');
                option.value = modelId;
                option.textContent = modelId;
                modelFilter.appendChild(option);
            });
        } else {
            const provider = providersData[selectedProvider];
            if (provider && provider.models) {
                Object.keys(provider.models).sort().forEach(modelId => {
                    const option = document.createElement('option');
                    option.value = modelId;
                    option.textContent = modelId;
                    modelFilter.appendChild(option);
                });
            }
        }
    }

    // Fetch Usage
    async function fetchUsage() {
        const since = sinceDateInput.value ? new Date(sinceDateInput.value).getTime() / 1000 : null;
        
        // The API takes since_time as a float (seconds since epoch)
        // We'll use the sinceDateInput value.
        
        showLoading(true);
        hideError();
        
        try {
            // Note: The API endpoint /api/v1/usage takes since_time as a query param
            let url = '/api/v1/usage';
            if (since) {
                url += `?since_time=${since}`;
            }

            const response = await fetch(url);
            if (!response.ok) throw new Error('Failed to fetch usage data');
            const data = await response.json();
            usageData = data.usage_data || [];
            
            renderCharts();
        } catch (err) {
            showError(`Error fetching usage: ${err.message}`);
        } finally {
            showLoading(false);
        }
    }

    function renderCharts() {
        inputTokensGrid.innerHTML = '';
        outputTokensGrid.innerHTML = '';
        elapsedTimeGrid.innerHTML = '';

        const selectedProvider = providerFilter.value;
        const selectedModel = modelFilter.value;

        // Filter data
        const filteredData = usageData.filter(item => {
            const providerMatch = selectedProvider === 'all' || item.provider_slug === selectedProvider;
            const modelMatch = selectedModel === 'all' || item.model_id === selectedModel;
            return providerMatch && modelMatch;
        });

        if (filteredData.length === 0) {
            showError('No usage data found for the selected criteria.');
            return;
        }

        // Group by provider_slug + model_id
        const groups = {};
        filteredData.forEach(item => {
            const key = `${item.provider_slug} | ${item.model_id}`;
            if (!groups[key]) {
                groups[key] = [];
            }
            groups[key].push(item);
        });

        // Sort groups by key
        const sortedKeys = Object.keys(groups).sort();

        // For each group, draw 3 charts
        sortedKeys.forEach(key => {
            const groupData = groups[key].sort((a, b) => a.created_time - b.created_time);
            const [provider, model] = key.split(' | ');

            createSmallMultiple(inputTokensGrid, key, groupData, 'input_tokens', 'Tokens');
            createSmallMultiple(outputTokensGrid, key, groupData, 'output_tokens', 'Tokens');
            createSmallMultiple(elapsedTimeGrid, key, groupData, 'elapsed_time', 'Seconds');
        });
    }

    function createSmallMultiple(container, title, data, field, unit) {
        const wrapper = document.createElement('div');
        wrapper.className = 'small-multiple-container';

        const titleDiv = document.createElement('div');
        titleDiv.className = 'small-multiple-title';
        titleDiv.textContent = title;
        wrapper.appendChild(titleDiv);

        const svgDiv = document.createElement('div');
        svgDiv.className = 'chart-svg';
        wrapper.appendChild(svgDiv);

        container.appendChild(wrapper);

        const margin = { top: 10, right: 10, bottom: 25, left: 35 };
        const width = svgDiv.clientWidth || 300;
        const height = 180 - margin.top - margin.bottom;

        const svg = d3.select(svgDiv)
            .append('svg')
            .attr('width', '100%')
            .attr('height', '100%')
            .attr('viewBox', `0 0 ${width} ${height + margin.top + margin.bottom}`)
            .append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        // Prepare data
        const plotData = data.map(d => {
            let val = 0;
            if (field === 'input_tokens' || field === 'output_tokens') {
                val = d.run_usage ? d.run_usage[field] : 0;
            } else {
                val = d.elapsed_time || 0;
            }
            return {
                time: new Date(d.created_time * 1000),
                value: val
            };
        });

        // Scales
        const x = d3.scaleTime()
            .domain(d3.extent(plotData, d => d.time))
            .range([0, width - margin.left - margin.right]);

        const y = d3.scaleLinear()
            .domain([0, d3.max(plotData, d => d.value) * 1.1 || 1])
            .range([height, 0]);

        // Axes
        svg.append('g')
            .attr('transform', `translate(0,${height})`)
            .attr('class', 'axis-label')
            .call(d3.axisBottom(x).ticks(4));

        svg.append('g')
            .attr('class', 'axis-label')
            .call(d3.axisLeft(y).ticks(4));

        // Grid lines
        svg.append('g')
            .attr('class', 'grid')
            .call(d3.axisLeft(y).tickSize(-width + margin.left + margin.right).tickFormat(''));

        // Line
        const line = d3.line()
            .x(d => x(d.time))
            .y(d => y(d.value))
            .curve(d3.curveMonotoneX);

        svg.append('path')
            .datum(plotData)
            .attr('class', 'line')
            .attr('stroke', getMetricColor(field))
            .attr('d', line);
    }

    function getMetricColor(field) {
        if (field === 'input_tokens') return '#6366f1';
        if (field === 'output_tokens') return '#8b5cf6';
        if (field === 'elapsed_time') return '#10b981';
        return '#4a90d9';
    }

    function showLoading(show) {
        loadingOverlay.style.display = show ? 'flex' : 'none';
    }

    function showError(msg) {
        errorDisplay.textContent = msg;
        errorDisplay.style.display = 'block';
    }

    function hideError() {
        errorDisplay.style.display = 'none';
    }

    refreshBtn.addEventListener('click', fetchUsage);

    // Initial Load
    fetchProviders().then(() => {
        populateModelFilter();
        fetchUsage();
    });
});
