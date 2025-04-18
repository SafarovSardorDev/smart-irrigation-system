// Xarita uchun o'zgaruvchilar
let map;
let plotMarkers = {};
let plots = [];
// Nasos holatlari uchun o'zgaruvchilar
const pumpStatuses = {
    'off': {
        className: 'bg-gray-400',
        text: 'O\'chirilgan',
        badgeClass: 'bg-gray-100 text-gray-800'
    },
    'on_low': {
        className: 'bg-yellow-500',
        text: 'Yoqilgan (past)',
        badgeClass: 'bg-yellow-100 text-yellow-800'
    },
    'on_high': {
        className: 'bg-green-500',
        text: 'Yoqilgan (yuqori)',
        badgeClass: 'bg-green-100 text-green-800'
    }
};
// Maydon holatlar uchun o'zgaruvchilar
const plotStatuses = {
    'yetarli': {
        className: 'status-yetarli',
        color: '#10b981'
    },
    'ortacha': {
        className: 'status-ortacha',
        color: '#f59e0b'
    },
    'sugorish_kerak': {
        className: 'status-sugorish-kerak',
        color: '#ef4444'
    }
};
// Sahifa yuklanganda ishga tushuvchi funksiya
document.addEventListener('DOMContentLoaded', function() {
    initializeMap();
    loadPlots();
    initializeCharts();
    connectWebSocket();
});
// Xaritani ishga tushirish
function initializeMap() {
    map = L.map('map').setView([41.3775, 64.5853], 12); // O'zbekiston koordinatalari
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
}

// WebSocket orqali real-time ma'lumotlarni olish
function connectWebSocket() {
    const socket = new WebSocket(`ws://${window.location.host}/ws/plots/`);
    
    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        if (data.type === 'plot_update') {
            updatePlotStatus(data.plot_id, data.status, data.humidity, data.temperature);
        } else if (data.type === 'pump_update') {
            updatePumpStatus(data.pump_id, data.status);
        }
    };
    
    socket.onclose = function() {
        console.log('WebSocket connection closed, attempting to reconnect...');
        setTimeout(connectWebSocket, 1000);
    };
}

// Maydonlar ma'lumotlarini yuklash
function loadPlots() {
    fetch('/api/plots/')
        .then(response => response.json())
        .then(data => {
            plots = data;
            renderPlotsList();
            addPlotsToMap();
        })
        .catch(error => console.error('Error loading plots:', error));
}

// Maydonlar ro'yxatini ko'rsatish
function renderPlotsList() {
    const plotsContainer = document.getElementById('plots-list');
    plotsContainer.innerHTML = '';
    
    plots.forEach(plot => {
        const plotCard = document.createElement('div');
        plotCard.className = `plot-card mb-4 p-4 rounded-lg shadow-md border-l-4 ${plotStatuses[plot.status].className}`;
        plotCard.innerHTML = `
            <div class="flex justify-between items-center">
                <h3 class="text-lg font-semibold">${plot.name}</h3>
                <span class="status-badge px-2 py-1 rounded-full text-xs font-medium" 
                      style="background-color: ${plotStatuses[plot.status].color}20; color: ${plotStatuses[plot.status].color}">
                    ${getStatusText(plot.status)}
                </span>
            </div>
            <div class="text-sm text-gray-500 mt-1">
                ${plot.crop_type} | ${plot.area} gektar
            </div>
            <div class="mt-3 grid grid-cols-2 gap-2">
                <div class="flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-blue-500 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                    </svg>
                    <span class="humidity-value">${plot.humidity}%</span>
                </div>
                <div class="flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-red-500 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                    <span class="temperature-value">${plot.temperature}°C</span>
                </div>
            </div>
            <div class="mt-3">
                <a href="/plots/${plot.id}/" class="text-sm text-blue-500 hover:text-blue-700">
                    Batafsil ko'rish →
                </a>
            </div>
        `;
        
        plotCard.addEventListener('click', () => {
            window.location.href = `/plots/${plot.id}/`;
        });
        
        plotsContainer.appendChild(plotCard);
    });
}

// Maydonni xaritaga qo'shish
function addPlotsToMap() {
    plots.forEach(plot => {
        const plotCoordinates = [plot.latitude, plot.longitude];
        
        const plotIcon = L.divIcon({
            className: `plot-marker ${plotStatuses[plot.status].className}`,
            html: `<div class="marker-inner" style="background-color: ${plotStatuses[plot.status].color}"></div>`,
            iconSize: [20, 20]
        });
        
        const marker = L.marker(plotCoordinates, { icon: plotIcon }).addTo(map);
        
        marker.bindPopup(`
            <div class="plot-popup">
                <h3>${plot.name}</h3>
                <p>Ekin turi: ${plot.crop_type}</p>
                <p>Namlik: <span class="font-medium">${plot.humidity}%</span></p>
                <p>Harorat: <span class="font-medium">${plot.temperature}°C</span></p>
                <p>Holat: <span class="font-medium">${getStatusText(plot.status)}</span></p>
                <a href="/plots/${plot.id}/" class="popup-link">Batafsil</a>
            </div>
        `);
        
        plotMarkers[plot.id] = marker;
    });
    
    // Barcha maydonlarni xaritada ko'rsatish
    if (plots.length > 0) {
        const bounds = [];
        plots.forEach(plot => bounds.push([plot.latitude, plot.longitude]));
        map.fitBounds(bounds);
    }
}

// Nasos holatini yangilash
function updatePumpStatus(pumpId, status) {
    const pumpElement = document.getElementById(`pump-${pumpId}`);
    
    if (pumpElement) {
        const statusInfo = pumpStatuses[status];
        
        pumpElement.classList.remove('bg-gray-400', 'bg-yellow-500', 'bg-green-500');
        pumpElement.classList.add(statusInfo.className);
        
        const badgeElement = pumpElement.querySelector('.pump-status-badge');
        if (badgeElement) {
            badgeElement.className = `pump-status-badge px-2 py-1 rounded-full text-xs ${statusInfo.badgeClass}`;
            badgeElement.textContent = statusInfo.text;
        }
        
        // Nasos holatiga qarab animatsiya qo'shish
        const pumpIcon = pumpElement.querySelector('.pump-icon');
        if (pumpIcon) {
            if (status !== 'off') {
                pumpIcon.classList.add('pulse-animation');
            } else {
                pumpIcon.classList.remove('pulse-animation');
            }
        }
    }
}

// Maydon holatini yangilash
function updatePlotStatus(plotId, status, humidity, temperature) {
    // Ro'yxatdagi maydon holatini yangilash
    const plotElement = document.querySelector(`.plot-card[data-id="${plotId}"]`);
    
    if (plotElement) {
        plotElement.classList.remove(...Object.values(plotStatuses).map(s => s.className));
        plotElement.classList.add(plotStatuses[status].className);
        
        const statusBadge = plotElement.querySelector('.status-badge');
        if (statusBadge) {
            statusBadge.style.backgroundColor = `${plotStatuses[status].color}20`;
            statusBadge.style.color = plotStatuses[status].color;
            statusBadge.textContent = getStatusText(status);
        }
        
        const humidityElement = plotElement.querySelector('.humidity-value');
        if (humidityElement) {
            humidityElement.textContent = `${humidity}%`;
        }
        
        const temperatureElement = plotElement.querySelector('.temperature-value');
        if (temperatureElement) {
            temperatureElement.textContent = `${temperature}°C`;
        }
    }
    
    // Xaritadagi markerning holatini yangilash
    if (plotMarkers[plotId]) {
        const marker = plotMarkers[plotId];
        const newIcon = L.divIcon({
            className: `plot-marker ${plotStatuses[status].className}`,
            html: `<div class="marker-inner" style="background-color: ${plotStatuses[status].color}"></div>`,
            iconSize: [20, 20]
        });
        
        marker.setIcon(newIcon);
        marker.setPopupContent(`
            <div class="plot-popup">
                <h3>${getPlotName(plotId)}</h3>
                <p>Ekin turi: ${getPlotCropType(plotId)}</p>
                <p>Namlik: <span class="font-medium">${humidity}%</span></p>
                <p>Harorat: <span class="font-medium">${temperature}°C</span></p>
                <p>Holat: <span class="font-medium">${getStatusText(status)}</span></p>
                <a href="/plots/${plotId}/" class="popup-link">Batafsil</a>
            </div>
        `);
    }
    
    // Agar joriy detail sahifada bo'lsa, grafiklarni yangilash
    if (window.location.pathname.includes(`/plots/${plotId}/`)) {
        updateCharts(humidity, temperature);
    }
}

// Grafiklarga ma'lumot qo'shish
function updateCharts(humidity, temperature) {
    if (humidityChart && temperatureChart) {
        const now = new Date();
        const timeStr = now.getHours() + ':' + now.getMinutes();
        
        // Namlik grafikini yangilash
        humidityChart.data.labels.push(timeStr);
        humidityChart.data.datasets[0].data.push(humidity);
        
        // 12 tadan ko'p bo'lsa, birinchisini o'chirish
        if (humidityChart.data.labels.length > 12) {
            humidityChart.data.labels.shift();
            humidityChart.data.datasets[0].data.shift();
        }
        
        humidityChart.update();
        
        // Harorat grafikini yangilash
        temperatureChart.data.labels.push(timeStr);
        temperatureChart.data.datasets[0].data.push(temperature);
        
        if (temperatureChart.data.labels.length > 12) {
            temperatureChart.data.labels.shift();
            temperatureChart.data.datasets[0].data.shift();
        }
        
        temperatureChart.update();
    }
}

// Grafiklarni ishga tushirish
let humidityChart, temperatureChart;

function initializeCharts() {
    const plotIdMatch = window.location.pathname.match(/\/plots\/(\d+)\//);
    
    if (plotIdMatch) {
        const plotId = plotIdMatch[1];
        
        // Oxirgi 12 ta ma'lumotni olish
        fetch(`/api/plots/${plotId}/history/?limit=12`)
            .then(response => response.json())
            .then(data => {
                renderCharts(data);
            })
            .catch(error => console.error('Error loading history:', error));
    }
}

function renderCharts(historyData) {
    const humidityCtx = document.getElementById('humidity-chart');
    const temperatureCtx = document.getElementById('temperature-chart');
    
    if (!humidityCtx || !temperatureCtx) return;
    
    const times = historyData.map(item => {
        const date = new Date(item.timestamp);
        return date.getHours() + ':' + date.getMinutes();
    });
    
    const humidityValues = historyData.map(item => item.humidity);
    const temperatureValues = historyData.map(item => item.temperature);
    
    // Namlik grafiki
    humidityChart = new Chart(humidityCtx, {
        type: 'line',
        data: {
            labels: times,
            datasets: [{
                label: 'Namlik (%)',
                data: humidityValues,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 2,
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return `Namlik: ${context.parsed.y}%`;
                        }
                    }
                },
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
    
    // Harorat grafiki
    temperatureChart = new Chart(temperatureCtx, {
        type: 'line',
        data: {
            labels: times,
            datasets: [{
                label: 'Harorat (°C)',
                data: temperatureValues,
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                borderWidth: 2,
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return `Harorat: ${context.parsed.y}°C`;
                        }
                    }
                },
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    ticks: {
                        callback: function(value) {
                            return value + '°C';
                        }
                    }
                }
            }
        }
    });
    
    // Vaqt oraliqlari bo'yicha filtrlash buttonlarini sozlash
    setupTimeFilters();
}

// Vaqt oraliqlari uchun filter
function setupTimeFilters() {
    const timeButtons = document.querySelectorAll('.time-filter-btn');
    
    timeButtons.forEach(button => {
        button.addEventListener('click', () => {
            timeButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            const plotId = window.location.pathname.match(/\/plots\/(\d+)\//)[1];
            const timeRange = button.dataset.range;
            
            fetch(`/api/plots/${plotId}/history/?time_range=${timeRange}`)
                .then(response => response.json())
                .then(data => {
                    updateChartsWithNewData(data);
                })
                .catch(error => console.error('Error loading filtered history:', error));
        });
    });
}

// Grafiklarni yangi ma'lumot bilan yangilash
function updateChartsWithNewData(historyData) {
    if (!humidityChart || !temperatureChart) return;
    
    const times = historyData.map(item => {
        const date = new Date(item.timestamp);
        return date.getHours() + ':' + date.getMinutes();
    });
    
    const humidityValues = historyData.map(item => item.humidity);
    const temperatureValues = historyData.map(item => item.temperature);
    
    // Namlik grafiki yangilash
    humidityChart.data.labels = times;
    humidityChart.data.datasets[0].data = humidityValues;
    humidityChart.update();
    
    // Harorat grafiki yangilash
    temperatureChart.data.labels = times;
    temperatureChart.data.datasets[0].data = temperatureValues;
    temperatureChart.update();
}

// Status textini qaytaradigan funksiya
function getStatusText(status) {
    switch(status) {
        case 'yetarli':
            return 'Yetarli';
        case 'ortacha':
            return 'O\'rtacha';
        case 'sugorish_kerak':
            return 'Sug\'orish kerak';
        default:
            return 'Noma\'lum';
    }
}

// Yordamchi funksiyalar
function getPlotName(plotId) {
    const plot = plots.find(p => p.id == plotId);
    return plot ? plot.name : 'Noma\'lum maydon';
}

function getPlotCropType(plotId) {
    const plot = plots.find(p => p.id == plotId);
    return plot ? plot.crop_type : 'Noma\'lum ekin';
}


