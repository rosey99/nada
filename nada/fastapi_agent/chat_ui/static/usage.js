// Usage Data Chart Application
// Based on d3-graph-gallery.com/graph/line_several_group.html

class UsageChartApp {
    constructor() {
        this.API_BASE_URL = "";
        this.chart = null;
        this.data = [];
        this.colors = [
            "#4a90d9", // blue
            "#e74c3c", // red
            "#2ecc71", // green
            "#f39c12", // orange
            "#9b59b6", // purple
            "#1abc9c", // teal
            "#e67e22", // dark orange
            "#3498db", // light blue
        ];
        this.groupColors = {};
        this.groupIndex = 0;
        this.init();
    }

    init() {
        this.setupDefaults();
        this.bindEvents();
        this.initChart();
    }

    setupDefaults() {
        // Set default time range to last 24 hours
        const now = new Date();
        const since = new Date(now.getTime() - 24 * 60 * 60 * 1000);

        document.getElementById("sinceDate").value = since.toISOString().split("T")[0];
        document.getElementById("sinceTime").value = since.toTimeString().split(" ")[0].substring(0, 5);
        document.getElementById("untilDate").value = now.toISOString().split("T")[0];
        document.getElementById("untilTime").value = now.toTimeString().split(" ")[0].substring(0, 5);
    }

    bindEvents() {
        document.getElementById("fetchUsage").addEventListener("click", () => this.fetchUsage());

        // Quick date buttons
        document.querySelectorAll(".quick-dates button").forEach((btn) => {
            btn.addEventListener("click", (e) => {
                const hours = parseInt(e.target.dataset.hours);
                this.setQuickDate(hours);
                // Highlight active button
                document.querySelectorAll(".quick-dates button").forEach((b) => b.classList.remove("active"));
                e.target.classList.add("active");
            });
        });
    }

    setQuickDate(hours) {
        const now = new Date();
        const since = new Date(now.getTime() - hours * 60 * 60 * 1000);

        document.getElementById("sinceDate").value = since.toISOString().split("T")[0];
        document.getElementById("sinceTime").value = since.toTimeString().split(" ")[0].substring(0, 5);
        document.getElementById("untilDate").value = now.toISOString().split("T")[0];
        document.getElementById("untilTime").value = now.toTimeString().split(" ")[0].substring(0, 5);

        // Remove active class from all buttons
        document.querySelectorAll(".quick-dates button").forEach((b) => b.classList.remove("active"));
        // Add active class to the clicked button
        document.querySelector(`.quick-dates button[data-hours="${hours}"]`).classList.add("active");
    }

    getSinceTime() {
        const dateStr = document.getElementById("sinceDate").value;
        const timeStr = document.getElementById("sinceTime").value;
        if (!dateStr || !timeStr) return null;
        const dateTime = new Date(`${dateStr}T${timeStr}`);
        return dateTime.getTime() / 1000; // Convert to unix epoch seconds
    }

    getUntilTime() {
        const dateStr = document.getElementById("untilDate").value;
        const timeStr = document.getElementById("untilTime").value;
        if (!dateStr || !timeStr) return null;
        const dateTime = new Date(`${dateStr}T${timeStr}`);
        return dateTime.getTime() / 1000;
    }

    async fetchUsage() {
        const sinceTime = this.getSinceTime();
        const untilTime = this.getUntilTime();

        if (!sinceTime || !untilTime) {
            this.showError("Please select both since and until dates/times.");
            return;
        }

        if (sinceTime >= untilTime) {
            this.showError("Since time must be before until time.");
            return;
        }

        this.showLoading(true);
        this.hideError();

        try {
            const url = `/api/v1/usage?since_time=${sinceTime}`;
            const response = await fetch(url, {
                method: "GET",
                credentials: "include",
            });

            if (!response.ok) {
                if (response.status === 401 || response.status === 403) {
                    this.showError("Authentication required. Please log in again.");
                    window.location.href = "/agent/v1/login";
                    return;
                }
                throw new Error(`HTTP error: ${response.status}`);
            }

            const result = await response.json();
            this.data = result.usage_data || [];
            this.showLoading(false);
            this.renderChart();
            this.renderStats();
            this.renderLegend();
        } catch (error) {
            this.showLoading(false);
            this.showError(`Failed to load usage data: ${error.message}`);
        }
    }

    initChart() {
        const container = document.getElementById("chart-container");
        const width = container.clientWidth - 20;
        const height = container.clientHeight - 40;

        const margin = { top: 20, right: 30, bottom: 40, left: 60 };
        const innerWidth = width - margin.left - margin.right;
        const innerHeight = height - margin.top - margin.bottom;

        this.chart = {
            svg: d3.select("#chart-container")
                .append("svg")
                .attr("width", width)
                .attr("height", height),
            g: d3.select("#chart-container")
                .append("g")
                .attr("transform", `translate(${margin.left},${margin.top})`),
            width: innerWidth,
            height: innerHeight,
        };

        // Clear any existing content in the chart container
        d3.select("#chart-container").selectAll("svg").remove();
        d3.select("#chart-container").selectAll("g").remove();

        // Re-create the SVG and g elements
        this.chart.svg = d3.select("#chart-container")
            .append("svg")
            .attr("width", width)
            .attr("height", height);
        this.chart.g = this.chart.svg.append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);

        // Add axes
        this.chart.xAxis = this.chart.g.append("g")
            .attr("transform", `translate(0,${this.chart.height})`);
        this.chart.yAxis = this.chart.g.append("g");

        // Add axis labels
        this.chart.g.append("text")
            .attr("x", this.chart.width / 2)
            .attr("y", this.chart.height + 35)
            .attr("text-anchor", "middle")
            .attr("fill", "#888")
            .attr("font-size", "12px")
            .text("Time");

        this.chart.g.append("text")
            .attr("transform", "rotate(-90)")
            .attr("x", -this.chart.height / 2)
            .attr("y", -45)
            .attr("text-anchor", "middle")
            .attr("fill", "#888")
            .attr("font-size", "12px")
            .text("Token Count");

        // Add grid lines
        this.chart.g.append("g")
            .attr("class", "grid")
            .attr("transform", `translate(0,${this.chart.height})`);
    }

    renderChart() {
        if (!this.chart) return;

        const container = document.getElementById("chart-container");
        const width = container.clientWidth - 20;
        const height = container.clientHeight - 40;

        this.chart.svg.attr("width", width).attr("height", height);
        this.chart.g.attr("transform", `translate(40,20)`);
        this.chart.width = width - 80;
        this.chart.height = height - 60;

        // Clear previous chart content
        this.chart.g.selectAll("*").remove();

        // Add axes back
        this.chart.xAxis = this.chart.g.append("g")
            .attr("transform", `translate(0,${this.chart.height})`);
        this.chart.yAxis = this.chart.g.append("g");

        // Add axis labels
        this.chart.g.append("text")
            .attr("x", this.chart.width / 2)
            .attr("y", this.chart.height + 35)
            .attr("text-anchor", "middle")
            .attr("fill", "#888")
            .attr("font-size", "12px")
            .text("Time");

        this.chart.g.append("text")
            .attr("transform", "rotate(-90)")
            .attr("x", -this.chart.height / 2)
            .attr("y", -45)
            .attr("text-anchor", "middle")
            .attr("fill", "#888")
            .attr("font-size", "12px")
            .text("Token Count");

        // Add grid lines
        this.chart.g.append("g")
            .attr("class", "grid")
            .attr("transform", `translate(0,${this.chart.height})`);

        if (this.data.length === 0) {
            this.chart.g.append("text")
                .attr("x", this.chart.width / 2)
                .attr("y", this.chart.height / 2)
                .attr("text-anchor", "middle")
                .attr("fill", "#888")
                .attr("font-size", "14px")
                .text("No usage data available for the selected time range");
            return;
        }

        // Group data by model_id + provider_slug
        const groupedData = {};
        this.data.forEach((item) => {
            const key = `${item.provider_slug || "unknown"}: ${item.model_id || "unknown"}`;
            if (!groupedData[key]) {
                groupedData[key] = [];
            }
            groupedData[key].push({
                time: item.created_time,
                value: item.run_usage.total_tokens || 0,
                item: item,
            });
        });

        // Sort each group by time
        Object.keys(groupedData).forEach((key) => {
            groupedData[key].sort((a, b) => a.time - b.time);
        });

        // Assign colors to groups
        const groupKeys = Object.keys(groupedData);
        groupKeys.forEach((key, index) => {
            this.groupColors[key] = this.colors[index % this.colors.length];
        });

        // Prepare data for d3 line chart
        const allTimes = this.data.map((d) => d.created_time);
        const allValues = this.data.map((d) => d.run_usage.total_tokens || 0);

        // Create scales
        const x = d3.scaleTime()
            .domain(d3.extent(allTimes))
            .range([0, this.chart.width]);

        const y = d3.scaleLinear()
            .domain([0, d3.max(allValues) || 1])
            .range([this.chart.height, 0]);

        // Create line generator
        const line = d3.line()
            .x((d) => x(d.time))
            .y((d) => y(d.value))
            .curve(d3.curveMonotoneX);

        // Draw grid lines
        this.chart.g.select(".grid")
            .call(d3.axisBottom(x).tickSize(-this.chart.height).tickFormat(""))
            .selectAll("text")
            .style("fill", "none");
        this.chart.g.select(".grid")
            .selectAll("line")
            .style("stroke", "#333")
            .style("stroke-opacity", 0.3);

        // Draw Y grid lines
        this.chart.g.select(".grid")
            .call(d3.axisLeft(y).tickSize(-this.chart.width).tickFormat(""))
            .selectAll("text")
            .style("fill", "none");
        this.chart.g.select(".grid")
            .selectAll("line")
            .style("stroke", "#333")
            .style("stroke-opacity", 0.3);

        // Draw axes
        this.chart.xAxis.call(
            d3.axisBottom(x)
                .tickFormat(d3.timeFormat("%Y-%m-%d %H:%M"))
                .ticks(8)
        );
        this.chart.yAxis.call(
            d3.axisLeft(y)
                .ticks(8)
                .tickFormat((d) => d.toLocaleString())
        );

        // Style axes
        this.chart.g.selectAll(".domain")
            .style("stroke", "#555");
        this.chart.g.selectAll(".tick line")
            .style("stroke", "#555");
        this.chart.g.selectAll(".tick text")
            .style("fill", "#888")
            .style("font-size", "11px");

        // Draw lines for each group
        const lineGroups = this.chart.g.selectAll(".line-group")
            .data(groupKeys)
            .enter()
            .append("g")
            .attr("class", "line-group");

        lineGroups.append("path")
            .attr("class", "line")
            .attr("fill", "none")
            .attr("stroke", (d) => this.groupColors[d])
            .attr("stroke-width", 2)
            .attr("d", (d) => line(groupedData[d]));

        // Add dots for each data point
        lineGroups.each((groupKey) => {
            const points = groupedData[groupKey];
            this.chart.g.selectAll(`.dot-${groupKey.replace(/[^a-zA-Z0-9]/g, "_")}`)
                .data(points)
                .enter()
                .append("circle")
                .attr("class", `dot-${groupKey.replace(/[^a-zA-Z0-9]/g, "_")}`)
                .attr("cx", (d) => x(d.time))
                .attr("cy", (d) => y(d.value))
                .attr("r", 3)
                .attr("fill", this.groupColors[groupKey])
                .attr("stroke", "#1a1a1a")
                .attr("stroke-width", 1);
        });

        // Add hover tooltips
        const tooltip = d3.select("#chart-container")
            .append("div")
            .attr("class", "usage-tooltip")
            .style("position", "absolute")
            .style("background", "rgba(0,0,0,0.85)")
            .style("color", "#eee")
            .style("padding", "8px 12px")
            .style("border-radius", "4px")
            .style("font-size", "12px")
            .style("pointer-events", "none")
            .style("opacity", 0)
            .style("transition", "opacity 0.2s");

        // Add hover circles
        lineGroups.each((groupKey) => {
            const points = groupedData[groupKey];
            this.chart.g.selectAll(`.hover-circle-${groupKey.replace(/[^a-zA-Z0-9]/g, "_")}`)
                .data(points)
                .enter()
                .append("circle")
                .attr("class", `hover-circle-${groupKey.replace(/[^a-zA-Z0-9]/g, "_")}`)
                .attr("cx", (d) => x(d.time))
                .attr("cy", (d) => y(d.value))
                .attr("r", 8)
                .attr("fill", "transparent")
                .style("cursor", "pointer")
                .on("mouseover", (event, d) => {
                    tooltip.style("opacity", 1);
                    const date = new Date(d.time * 1000);
                    tooltip.html(
                        `<strong>${groupKey}</strong><br/>` +
                        `Time: ${date.toLocaleString()}<br/>` +
                        `Total Tokens: ${d.value.toLocaleString()}<br/>` +
                        `Input Tokens: ${(d.item.run_usage.input_tokens || 0).toLocaleString()}<br/>` +
                        `Output Tokens: ${(d.item.run_usage.output_tokens || 0).toLocaleString()}<br/>` +
                        `Time: ${d.item.elapsed_time.toFixed(2)}s`
                    );
                })
                .on("mousemove", (event) => {
                    tooltip
                        .style("left", `${event.pageX + 15}px`)
                        .style("top", `${event.pageY - 30}px`);
                })
                .on("mouseout", () => {
                    tooltip.style("opacity", 0);
                });
        });
    }

    renderLegend() {
        const legend = document.getElementById("usageLegend");
        legend.innerHTML = "";

        Object.keys(this.groupColors).forEach((key) => {
            const item = document.createElement("div");
            item.className = "usage-legend-item";
            item.innerHTML = `
                <div class="usage-legend-color" style="background-color: ${this.groupColors[key]}"></div>
                <span>${key}</span>
            `;
            legend.appendChild(item);
        });
    }

    renderStats() {
        const stats = document.getElementById("usageStats");
        stats.innerHTML = "";

        const totalTokens = this.data.reduce((sum, d) => sum + (d.run_usage.total_tokens || 0), 0);
        const totalInputTokens = this.data.reduce((sum, d) => sum + (d.run_usage.input_tokens || 0), 0);
        const totalOutputTokens = this.data.reduce((sum, d) => sum + (d.run_usage.output_tokens || 0), 0);
        const avgTime = this.data.length > 0 ? this.data.reduce((sum, d) => sum + d.elapsed_time, 0) / this.data.length : 0;

        const statItems = [
            { label: "Total Requests", value: this.data.length.toLocaleString() },
            { label: "Total Tokens", value: totalTokens.toLocaleString() },
            { label: "Input Tokens", value: totalInputTokens.toLocaleString() },
            { label: "Output Tokens", value: totalOutputTokens.toLocaleString() },
            { label: "Avg Time", value: `${avgTime.toFixed(2)}s` },
        ];

        statItems.forEach((stat) => {
            const item = document.createElement("div");
            item.className = "usage-stat";
            item.innerHTML = `
                <div class="usage-stat-label">${stat.label}</div>
                <div class="usage-stat-value">${stat.value}</div>
            `;
            stats.appendChild(item);
        });
    }

    showError(message) {
        const errorEl = document.getElementById("usageError");
        errorEl.textContent = message;
        errorEl.style.display = "block";
    }

    hideError() {
        document.getElementById("usageError").style.display = "none";
    }

    showLoading(show) {
        document.getElementById("usageLoading").style.display = show ? "block" : "none";
        document.getElementById("fetchUsage").disabled = show;
    }
}

// Initialize the app when the DOM is ready
document.addEventListener("DOMContentLoaded", () => {
    window.usageApp = new UsageChartApp();
});
