document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('weeklyHoursChart');
    if (!canvas) return;

    fetch('/api/daily-hours/')
        .then(res => {
            if (!res.ok) {
                throw new Error('Failed to fetch chart data');
            }
            return res.json();
        })
        .then(data => {
            console.log('API data:', data);

            // Create gradient
            const ctx = canvas.getContext('2d');
            const gradient = ctx.createLinearGradient(0, 0, 0, 400);
            gradient.addColorStop(0, 'rgba(14, 165, 233, 0.8)');
            gradient.addColorStop(1, 'rgba(6, 182, 212, 0.8)');

            new Chart(canvas, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Study Hours per Day',
                        data: data.data,
                        borderColor: '#0ea5e9',
                        backgroundColor: gradient,
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 5,
                        pointBackgroundColor: '#0ea5e9',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointHoverRadius: 7,
                        pointHoverBackgroundColor: '#06b6d4',
                        pointHoverBorderColor: '#fff',
                        pointHoverBorderWidth: 3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            labels: {
                                font: {
                                    family: 'Outfit',
                                    size: 14,
                                    weight: '600'
                                },
                                color: '#4a5568',
                                padding: 15
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(26, 32, 44, 0.95)',
                            titleFont: {
                                family: 'Outfit',
                                size: 14,
                                weight: '600'
                            },
                            bodyFont: {
                                family: 'Outfit',
                                size: 13
                            },
                            padding: 12,
                            cornerRadius: 8,
                            displayColors: false,
                            callbacks: {
                                label: function (context) {
                                    return context.parsed.y + ' hours';
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                font: {
                                    family: 'Outfit',
                                    size: 12
                                },
                                color: '#718096',
                                callback: function (value) {
                                    return value + 'h';
                                }
                            },
                            grid: {
                                color: 'rgba(226, 232, 240, 0.5)',
                                drawBorder: false
                            }
                        },
                        x: {
                            ticks: {
                                font: {
                                    family: 'Outfit',
                                    size: 12,
                                    weight: '500'
                                },
                                color: '#718096'
                            },
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
        })
        .catch(err => {
            console.error('Chart error:', err);
            // Display error message to user
            const container = canvas.parentElement;
            container.innerHTML = '<p class="text-danger text-center">Failed to load chart data. Please refresh the page.</p>';
        });
});
