/**
 * 数据可视化图表模块
 * 基于 Plotly.js 实现交互式图表
 */

const ChartsModule = {
    // 图表通用配置
    defaultConfig: {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['lasso2d', 'select2d'],
        locale: 'zh-CN'
    },

    // 颜色配置
    colors: {
        buy: '#10B981',      // 绿色 - 买入信号
        sell: '#EF4444',     // 红色 - 卖出信号
        hold: '#F59E0B',     // 黄色 - 持有信号
        primary: '#3B82F6',  // 蓝色 - 主色调
        secondary: '#8B5CF6', // 紫色 - 次色调
        pe: '#06B6D4',       // 青色 - PE指标
        pb: '#EC4899',       // 粉色 - PB指标
        price: '#F97316'     // 橙色 - 价格
    },

    /**
     * 4.1 - 信号统计饼图 (P0)
     * @param {string} containerId - 容器元素ID
     * @param {Object} statsData - 统计数据 {buy: number, sell: number, hold: number}
     */
    createSignalPieChart(containerId, statsData) {
        const data = [{
            values: [statsData.buy || 0, statsData.sell || 0, statsData.hold || 0],
            labels: ['买入信号', '卖出信号', '持有信号'],
            type: 'pie',
            hole: 0.4, // 环形图
            marker: {
                colors: [this.colors.buy, this.colors.sell, this.colors.hold],
                line: {
                    color: '#FFFFFF',
                    width: 2
                }
            },
            textinfo: 'label+percent',
            textposition: 'outside',
            hoverinfo: 'label+value+percent'
        }];

        const layout = {
            title: {
                text: '信号分布统计',
                font: { size: 16, color: '#1F2937' }
            },
            showlegend: true,
            legend: {
                orientation: 'h',
                y: -0.1,
                x: 0.5,
                xanchor: 'center'
            },
            margin: { t: 60, b: 40, l: 40, r: 40 },
            height: 300,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent'
        };

        Plotly.newPlot(containerId, data, layout, this.defaultConfig);
    },

    /**
     * 4.2 - 评分分布散点图 (P0)
     * @param {string} containerId - 容器元素ID
     * @param {Array} records - 记录数组 [{industry, score, signal, pe_percentile, pb_percentile}]
     */
    createScoreScatterChart(containerId, records) {
        if (!records || records.length === 0) {
            this.showEmptyChart(containerId, '暂无评分数据');
            return;
        }

        // 按信号分组
        const buyData = records.filter(r => r.signal === 'buy');
        const sellData = records.filter(r => r.signal === 'sell');
        const holdData = records.filter(r => r.signal === 'hold');

        const traces = [];

        if (buyData.length > 0) {
            traces.push({
                x: buyData.map(r => r.pe_percentile),
                y: buyData.map(r => r.score),
                mode: 'markers',
                type: 'scatter',
                name: '买入',
                text: buyData.map(r => r.industry),
                marker: {
                    size: 10,
                    color: this.colors.buy,
                    symbol: 'circle'
                },
                hoverinfo: 'text+x+y'
            });
        }

        if (sellData.length > 0) {
            traces.push({
                x: sellData.map(r => r.pe_percentile),
                y: sellData.map(r => r.score),
                mode: 'markers',
                type: 'scatter',
                name: '卖出',
                text: sellData.map(r => r.industry),
                marker: {
                    size: 10,
                    color: this.colors.sell,
                    symbol: 'circle'
                },
                hoverinfo: 'text+x+y'
            });
        }

        if (holdData.length > 0) {
            traces.push({
                x: holdData.map(r => r.pe_percentile),
                y: holdData.map(r => r.score),
                mode: 'markers',
                type: 'scatter',
                name: '持有',
                text: holdData.map(r => r.industry),
                marker: {
                    size: 10,
                    color: this.colors.hold,
                    symbol: 'circle'
                },
                hoverinfo: 'text+x+y'
            });
        }

        const layout = {
            title: {
                text: '评分分布（按PE分位数）',
                font: { size: 16, color: '#1F2937' }
            },
            xaxis: {
                title: 'PE分位数 (%)',
                range: [0, 100],
                gridcolor: '#E5E7EB'
            },
            yaxis: {
                title: '综合评分',
                range: [0, 100],
                gridcolor: '#E5E7EB'
            },
            showlegend: true,
            legend: {
                orientation: 'h',
                y: -0.15,
                x: 0.5,
                xanchor: 'center'
            },
            margin: { t: 60, b: 60, l: 60, r: 40 },
            height: 400,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            hovermode: 'closest'
        };

        Plotly.newPlot(containerId, traces, layout, this.defaultConfig);
    },

    /**
     * 4.3 - 分位数趋势线图 (P0)
     * @param {string} containerId - 容器元素ID
     * @param {Array} historyData - 历史数据 [{date, industry, pe_percentile, pb_percentile}]
     */
    createPercentileTrendChart(containerId, historyData) {
        if (!historyData || historyData.length === 0) {
            this.showEmptyChart(containerId, '暂无历史趋势数据');
            return;
        }

        // 按日期排序
        const sortedData = historyData.sort((a, b) => new Date(a.date) - new Date(b.date));

        const traces = [
            {
                x: sortedData.map(d => d.date),
                y: sortedData.map(d => d.pe_percentile),
                mode: 'lines+markers',
                type: 'scatter',
                name: 'PE分位数',
                line: {
                    color: this.colors.pe,
                    width: 2
                },
                marker: { size: 6 }
            },
            {
                x: sortedData.map(d => d.date),
                y: sortedData.map(d => d.pb_percentile),
                mode: 'lines+markers',
                type: 'scatter',
                name: 'PB分位数',
                line: {
                    color: this.colors.pb,
                    width: 2
                },
                marker: { size: 6 }
            }
        ];

        const layout = {
            title: {
                text: '估值分位数趋势',
                font: { size: 16, color: '#1F2937' }
            },
            xaxis: {
                title: '日期',
                type: 'date',
                gridcolor: '#E5E7EB',
                tickformat: '%Y-%m-%d'
            },
            yaxis: {
                title: '分位数 (%)',
                range: [0, 100],
                gridcolor: '#E5E7EB'
            },
            showlegend: true,
            legend: {
                orientation: 'h',
                y: -0.15,
                x: 0.5,
                xanchor: 'center'
            },
            margin: { t: 60, b: 60, l: 60, r: 40 },
            height: 400,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            hovermode: 'x unified'
        };

        Plotly.newPlot(containerId, traces, layout, this.defaultConfig);
    },

    /**
     * 4.4 - 行业对比柱状图 (P0)
     * @param {string} containerId - 容器元素ID
     * @param {Array} industriesData - 行业数据 [{name, score, signal}]
     */
    createIndustryBarChart(containerId, industriesData) {
        if (!industriesData || industriesData.length === 0) {
            this.showEmptyChart(containerId, '暂无行业对比数据');
            return;
        }

        // 按评分排序
        const sortedData = industriesData.sort((a, b) => b.score - a.score);

        const colors = sortedData.map(d => {
            if (d.signal === 'buy') return this.colors.buy;
            if (d.signal === 'sell') return this.colors.sell;
            return this.colors.hold;
        });

        const data = [{
            x: sortedData.map(d => d.name),
            y: sortedData.map(d => d.score),
            type: 'bar',
            marker: {
                color: colors,
                line: {
                    color: '#FFFFFF',
                    width: 1
                }
            },
            text: sortedData.map(d => `${d.score}`),
            textposition: 'outside',
            hoverinfo: 'x+y'
        }];

        const layout = {
            title: {
                text: '行业评分排行',
                font: { size: 16, color: '#1F2937' }
            },
            xaxis: {
                title: '行业',
                tickangle: -45,
                gridcolor: '#E5E7EB'
            },
            yaxis: {
                title: '综合评分',
                range: [0, 100],
                gridcolor: '#E5E7EB'
            },
            margin: { t: 60, b: 100, l: 60, r: 40 },
            height: 400,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent'
        };

        Plotly.newPlot(containerId, data, layout, this.defaultConfig);
    },

    /**
     * 4.5 - 背离分析组合图 (P1)
     * @param {string} containerId - 容器元素ID
     * @param {Array} divergenceData - 背离数据 [{date, price, pe, pb, prosperity}]
     */
    createDivergenceMixedChart(containerId, divergenceData) {
        if (!divergenceData || divergenceData.length === 0) {
            this.showEmptyChart(containerId, '暂无背离分析数据');
            return;
        }

        const sortedData = divergenceData.sort((a, b) => new Date(a.date) - new Date(b.date));

        const traces = [
            {
                x: sortedData.map(d => d.date),
                y: sortedData.map(d => d.price),
                mode: 'lines',
                type: 'scatter',
                name: '价格指数',
                line: {
                    color: this.colors.price,
                    width: 3
                },
                yaxis: 'y'
            },
            {
                x: sortedData.map(d => d.date),
                y: sortedData.map(d => d.pe),
                mode: 'lines',
                type: 'scatter',
                name: 'PE分位数',
                line: {
                    color: this.colors.pe,
                    width: 2,
                    dash: 'dash'
                },
                yaxis: 'y2'
            },
            {
                x: sortedData.map(d => d.date),
                y: sortedData.map(d => d.pb),
                mode: 'lines',
                type: 'scatter',
                name: 'PB分位数',
                line: {
                    color: this.colors.pb,
                    width: 2,
                    dash: 'dash'
                },
                yaxis: 'y2'
            }
        ];

        const layout = {
            title: {
                text: '背离分析（价格 vs 估值）',
                font: { size: 16, color: '#1F2937' }
            },
            xaxis: {
                title: '日期',
                type: 'date',
                gridcolor: '#E5E7EB',
                tickformat: '%Y-%m-%d'
            },
            yaxis: {
                title: '价格指数',
                side: 'left',
                gridcolor: '#E5E7EB'
            },
            yaxis2: {
                title: '估值分位数 (%)',
                side: 'right',
                range: [0, 100],
                overlaying: 'y',
                gridcolor: '#E5E7EB'
            },
            showlegend: true,
            legend: {
                orientation: 'h',
                y: -0.15,
                x: 0.5,
                xanchor: 'center'
            },
            margin: { t: 60, b: 60, l: 60, r: 60 },
            height: 400,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            hovermode: 'x unified'
        };

        Plotly.newPlot(containerId, traces, layout, this.defaultConfig);
    },

    /**
     * 4.6 - 历史走势面积图 (P1)
     * @param {string} containerId - 容器元素ID
     * @param {Array} historyData - 历史数据 [{date, pe, pb, price}]
     */
    createHistoryAreaChart(containerId, historyData) {
        if (!historyData || historyData.length === 0) {
            this.showEmptyChart(containerId, '暂无历史走势数据');
            return;
        }

        const sortedData = historyData.sort((a, b) => new Date(a.date) - new Date(b.date));

        const traces = [
            {
                x: sortedData.map(d => d.date),
                y: sortedData.map(d => d.pe),
                mode: 'lines',
                type: 'scatter',
                name: 'PE分位数',
                fill: 'tozeroy',
                line: {
                    color: this.colors.pe,
                    width: 2
                },
                fillcolor: 'rgba(6, 182, 212, 0.3)'
            },
            {
                x: sortedData.map(d => d.date),
                y: sortedData.map(d => d.pb),
                mode: 'lines',
                type: 'scatter',
                name: 'PB分位数',
                fill: 'tozeroy',
                line: {
                    color: this.colors.pb,
                    width: 2
                },
                fillcolor: 'rgba(236, 72, 153, 0.3)'
            }
        ];

        const layout = {
            title: {
                text: '估值历史走势',
                font: { size: 16, color: '#1F2937' }
            },
            xaxis: {
                title: '日期',
                type: 'date',
                gridcolor: '#E5E7EB',
                tickformat: '%Y-%m-%d'
            },
            yaxis: {
                title: '分位数 (%)',
                range: [0, 100],
                gridcolor: '#E5E7EB'
            },
            showlegend: true,
            legend: {
                orientation: 'h',
                y: -0.15,
                x: 0.5,
                xanchor: 'center'
            },
            margin: { t: 60, b: 60, l: 60, r: 40 },
            height: 400,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            hovermode: 'x unified'
        };

        Plotly.newPlot(containerId, traces, layout, this.defaultConfig);
    },

    /**
     * 显示空图表提示
     * @param {string} containerId - 容器元素ID
     * @param {string} message - 提示消息
     */
    showEmptyChart(containerId, message) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="flex items-center justify-center h-full text-gray-400">
                    <div class="text-center">
                        <svg class="h-12 w-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                        </svg>
                        <p>${message}</p>
                    </div>
                </div>
            `;
        }
    },

    /**
     * 更新图表数据
     * @param {string} containerId - 容器元素ID
     * @param {Object} newData - 新数据
     */
    updateChart(containerId, newData) {
        Plotly.react(containerId, newData);
    },

    /**
     * 销毁图表
     * @param {string} containerId - 容器元素ID
     */
    destroyChart(containerId) {
        Plotly.purge(containerId);
    }
};

// 导出模块（兼容不同环境）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChartsModule;
} else {
    window.ChartsModule = ChartsModule;
}