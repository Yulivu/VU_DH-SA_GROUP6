import pandas as pd
import plotly.graph_objects as go
import json
import colorsys


def generate_distinct_colors(n):
    colors = []
    for i in range(n):
        hue = i / n
        rgb = colorsys.hls_to_rgb(hue, 0.6, 0.6)
        rgba = f'rgba({int(rgb[0] * 255)}, {int(rgb[1] * 255)}, {int(rgb[2] * 255)}, 0.6)'
        colors.append(rgba)
    return colors


def generate_year_intervals():
    intervals = []
    for start in range(1935, 2025, 5):
        end = start + 4
        intervals.append(f"{start}-{end}")
    return intervals


def load_and_process_data(file_path):
    df = pd.read_excel(file_path)
    df[['Latitude', 'Longitude']] = df['Coordinates'].str.split(',', expand=True).astype(float)
    return df


def create_interactive_map(df):
    year_intervals = generate_year_intervals()

    unique_publishers = df[df['Publisher'] != "NO DATA"]['Publisher'].unique()
    colors = generate_distinct_colors(len(unique_publishers))
    publisher_colors = dict(zip(unique_publishers, colors))

    continent_colors = {
        'LATIN AMERICA': '#FF6B6B',
        'EUROPE': '#4ECDC4',
        'NORTH AMERICA': '#45B7D1',
        'ASIA': '#96CEB4',
        'OCEANIA': '#FFEEAD'
    }

    data_json = df.to_json(orient='records')
    year_intervals_json = json.dumps(year_intervals)
    color_mapping_json = json.dumps(publisher_colors)
    continent_colors_json = json.dumps(continent_colors)

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Exhibition Map</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ 
            margin: 0; 
            padding: 0;
            width: 100vw;
            height: 100vh;
            overflow: hidden;
            position: relative;
            font-family: Arial, sans-serif;
        }}
        #map {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1;
        }}
        .title-container {{
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(255, 255, 255, 0.9);
            padding: 10px 20px;
            border-radius: 10px;
            z-index: 1000;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .title-text {{
            margin: 0;
            font-weight: bold;
            font-size: 18px;
            color: #333;
        }}
        .draggable {{ 
            position: fixed;
            z-index: 1000;
            transform: none !important;
        }}
        .panel {{
            position: absolute;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 10px;
            padding: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            overflow: hidden;
        }}
        .panel.collapsed {{
            height: 50px !important;
            resize: none !important;
        }}
        .panel-header {{ 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            padding: 10px;
            font-weight: bold;
            user-select: none;
            height: 20px;
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        .panel-content {{ 
            display: none;
            padding: 10px;
            flex: 1;
            opacity: 0;
            transform: translateY(-10px);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            overflow: auto;
        }}
        .panel-content.active {{ 
            display: block;
            opacity: 1;
            transform: translateY(0);
        }}
        .year-checkbox-grid {{ 
            display: grid; 
            grid-template-columns: repeat(4, 1fr); 
            gap: 5px;
            transition: all 0.3s ease;
        }}
        .year-checkbox {{ 
            display: flex; 
            align-items: center;
            font-size: 12px;
            transition: all 0.2s ease;
        }}
        .year-checkbox:hover {{
            transform: translateX(2px);
        }}
        .year-checkbox input {{ 
            margin-right: 5px; 
        }}
        .filter-buttons {{ 
            display: flex; 
            justify-content: space-between; 
            margin-bottom: 10px; 
        }}
        .filter-btn {{ 
            background: rgba(0,0,0,0.1);
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .filter-btn:hover {{
            background: rgba(0,0,0,0.2);
            transform: translateY(-1px);
        }}
        #timeline-container {{
            width: 500px;
            height: 400px;
            min-width: 400px;
            min-height: 50px;
            resize: both;
        }}
        #timeline-container .panel-content {{
            height: calc(100% - 40px);
        }}
        #timeline {{
            width: 100%;
            height: 100%;
            min-height: 250px;
            transition: all 0.3s ease;
        }}
        .handle {{
            cursor: move;
            padding: 5px 10px;
            background: rgba(0, 0, 0, 0.05);
            border-radius: 5px;
            margin-right: 10px;
            transition: all 0.2s ease;
        }}
        .handle:hover {{
            background: rgba(0, 0, 0, 0.1);
        }}
        #filter-container {{
            width: 300px;
            height: auto;
            transition: height 0.3s ease;
        }}
        .toggle-icon {{
            transition: all 0.3s ease;
        }}
        .panel:hover {{
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }}

        @keyframes flow {{
            0% {{
                stroke-dashoffset: 20;
            }}
            100% {{
                stroke-dashoffset: 0;
            }}
        }}
        .flowing-line {{
            stroke-dasharray: 4 4;
            animation: flow 1s linear infinite;
        }}
    </style>
</head>
<body>
    <div class="title-container">
        <h1 class="title-text">Global Exhibition Network of Indigenous Latin American Art</h1>
    </div>

    <div id="map"></div>

    <div id="filter-container" class="draggable panel" style="left: 20px; bottom: 20px;">
        <div class="panel-header">
            <div>
                <span class="handle">⋮⋮</span>
                <span>Filter by Years</span>
            </div>
            <span class="toggle-icon">▼</span>
        </div>
        <div class="panel-content">
            <div class="filter-buttons">
                <button id="select-all-btn" class="filter-btn">Select All</button>
                <button id="deselect-all-btn" class="filter-btn">Deselect All</button>
            </div>
            <div id="year-checkboxes" class="year-checkbox-grid"></div>
        </div>
    </div>

    <div id="timeline-container" class="draggable panel" style="right: 20px; bottom: 20px;">
        <div class="panel-header">
            <div>
                <span class="handle">⋮⋮</span>
                <span>Exhibition Timeline</span>
            </div>
            <span class="toggle-icon">▼</span>
        </div>
        <div class="panel-content">
            <div id="timeline"></div>
        </div>
    </div>

    <script>
        const originalData = {data_json};
        const yearIntervals = {year_intervals_json};
        const publisherColors = {color_mapping_json};
        const continentColors = {continent_colors_json};

        function makeDraggable(elem) {{
            const header = elem.querySelector('.panel-header');
            const handle = elem.querySelector('.handle');
            let isDragging = false;
            let currentX;
            let currentY;
            let initialX;
            let initialY;
            let xOffset = 0;
            let yOffset = 0;

            function dragStart(e) {{
                if (e.target === handle || e.target.parentElement === handle) {{
                    const rect = elem.getBoundingClientRect();
                    initialX = e.clientX - rect.left;
                    initialY = e.clientY - rect.top;
                    isDragging = true;
                    elem.style.transition = 'none';
                    elem.style.opacity = '0.8';
                }}
            }}

            function drag(e) {{
                if (isDragging) {{
                    e.preventDefault();

                    const newX = e.clientX - initialX;
                    const newY = e.clientY - initialY;

                    const maxX = window.innerWidth - elem.offsetWidth;
                    const maxY = window.innerHeight - elem.offsetHeight;

                    elem.style.left = Math.min(Math.max(0, newX), maxX) + 'px';
                    elem.style.top = Math.min(Math.max(0, newY), maxY) + 'px';
                    elem.style.bottom = 'auto';
                    elem.style.right = 'auto';

                    if (elem.id === 'timeline-container' && 
                        elem.querySelector('.panel-content').classList.contains('active')) {{
                        requestAnimationFrame(() => {{
                            Plotly.Plots.resize('timeline');
                        }});
                    }}
                }}
            }}

            function dragEnd(e) {{
                isDragging = false;
                elem.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
                elem.style.opacity = '1';
            }}

            handle.addEventListener('mousedown', dragStart);
            document.addEventListener('mousemove', drag);
            document.addEventListener('mouseup', dragEnd);

            if (elem.id === 'timeline-container') {{
                const resizeObserver = new ResizeObserver(entries => {{
                    if (elem.querySelector('.panel-content').classList.contains('active')) {{
                        setTimeout(() => Plotly.Plots.resize('timeline'), 0);
                    }}
                }});
                resizeObserver.observe(elem);
            }}
        }}

        document.querySelectorAll('.draggable').forEach(elem => {{
            makeDraggable(elem);
        }});

        document.querySelectorAll('.panel-header').forEach(header => {{
            header.addEventListener('click', (e) => {{
                if (e.target.classList.contains('handle') || 
                    e.target.parentElement.classList.contains('handle')) return;

                const panel = header.closest('.panel');
                const content = header.nextElementSibling;
                const toggleIcon = header.querySelector('.toggle-icon');

                content.style.display = 'block';
                const contentHeight = content.scrollHeight;

                if (!content.classList.contains('active')) {{
                    content.style.height = '0px';
                    content.classList.add('active');
                    requestAnimationFrame(() => {{
                        content.style.height = contentHeight + 'px';
                        panel.style.height = (contentHeight + 60) + 'px';
                    }});
                    panel.classList.remove('collapsed');
                }} else {{
                    content.style.height = '0px';
                    panel.style.height = '50px';
                    panel.classList.add('collapsed');
                    content.addEventListener('transitionend', () => {{
                        content.classList.remove('active');
                    }}, {{ once: true }});
                }}

                toggleIcon.textContent = content.classList.contains('active') ? '▲' : '▼';

                if (content.classList.contains('active') && content.querySelector('#timeline')) {{
                    setTimeout(() => {{
                        updateTimeline();
                    }}, 300);
                }}
            }});
        }});

        function createCurvedLine(start, end) {{
            const points = [];
            const steps = 50;

            const midLat = (start.lat + end.lat) / 2;
            const midLon = (start.lon + end.lon) / 2;

            const distance = Math.sqrt(
                Math.pow(end.lat - start.lat, 2) + 
                Math.pow(end.lon - start.lon, 2)
            );
            const curvature = distance * 0.2;

            const controlLat = midLat + curvature;
            const controlLon = midLon;

            for (let i = 0; i <= steps; i++) {{
                const t = i / steps;
                const lat = Math.pow(1-t, 2) * start.lat + 
                          2 * (1-t) * t * controlLat + 
                          Math.pow(t, 2) * end.lat;
                const lon = Math.pow(1-t, 2) * start.lon + 
                          2 * (1-t) * t * controlLon + 
                          Math.pow(t, 2) * end.lon;
                points.push([lat, lon]);
            }}

            return points;
        }}

function createPublisherLines(data) {{
            const validData = data.filter(item => item.Publisher !== "NO DATA");
            
            const publisherGroups = {{}};
            validData.forEach(item => {{
                if (!publisherGroups[item.Publisher]) {{
                    publisherGroups[item.Publisher] = [];
                }}
                publisherGroups[item.Publisher].push(item);
            }});

            const lines = [];
            const annotations = [];

            Object.entries(publisherGroups).forEach(([publisher, items]) => {{
                if (items.length > 1) {{
                    const color = publisherColors[publisher];
                    
                    for (let i = 0; i < items.length - 1; i++) {{
                        const item1 = items[i];
                        const item2 = items[i + 1];
                        
                        const curvePoints = createCurvedLine(
                            {{lat: item1.Latitude, lon: item1.Longitude}},
                            {{lat: item2.Latitude, lon: item2.Longitude}}
                        );

                        lines.push({{
                            type: 'scattermapbox',
                            lat: curvePoints.map(p => p[0]),
                            lon: curvePoints.map(p => p[1]),
                            mode: 'lines',
                            line: {{
                                width: 2,
                                color: color
                            }},
                            hoverinfo: 'text',
                            text: `${{publisher}}`,
                            showlegend: false
                        }});

                        const midPoint = curvePoints[Math.floor(curvePoints.length / 2)];
                        annotations.push({{
                            type: 'scattermapbox',
                            lat: [midPoint[0]],
                            lon: [midPoint[1]],
                            mode: 'text',
                            text: [publisher],
                            textposition: 'top center',
                            textfont: {{
                                size: 12,
                                color: color.replace('0.6', '0.9')
                            }},
                            showlegend: false
                        }});
                    }}
                }}
            }});

            return [...lines, ...annotations];
        }}

        function createTraces(data) {{
            const groupedData = {{}};
            data.forEach(item => {{
                const key = `${{item.Latitude}},${{item.Longitude}}`;
                if (!groupedData[key]) groupedData[key] = [];
                groupedData[key].push(item);
            }});

            return Object.entries(groupedData).map(([coord, group]) => {{
                const [lat, lon] = coord.split(',').map(Number);
                const count = group.length;

                const hoverText = [
                    `<b>Total Exhibitions:</b> ${{count}}`,
                    `<b>Exhibition Details:</b>`,
                    ...group.map(item => 
                        `- ${{item.Title}}->${{item.Publisher}} (${{item['Date of publication']}})`
                    )
                ].join('<br>');

                return {{
                    type: 'scattermapbox',
                    lat: [lat],
                    lon: [lon],
                    mode: 'markers',
                    marker: {{
                        size: 12,
                        color: `rgb(${{Math.max(0, 255 - count*10)}}, 0, 0)`,
                        opacity: 0.8
                    }},
                    text: [hoverText],
                    hoverinfo: 'text',
                    hoverlabel: {{
                        bgcolor: "white",
                        font: {{
                            size: 13,
                            family: "Courier New, monospace"
                        }},
                        align: "left"
                    }},
                    hovertemplate: "%{{text}}<extra></extra>"
                }};
            }});
        }}

        function createTimelinePlot(data, selectedIntervals) {{
            const sortedIntervals = selectedIntervals.sort((a, b) => {{
                const [startA] = a.split('-').map(Number);
                const [startB] = b.split('-').map(Number);
                return startA - startB;
            }});
            
            const continentData = {{}};
            ['LATIN AMERICA', 'EUROPE', 'NORTH AMERICA', 'ASIA', 'OCEANIA'].forEach(continent => {{
                continentData[continent] = sortedIntervals.map(interval => {{
                    const [start, end] = interval.split('-').map(Number);
                    const count = data.filter(item => 
                        item.Continent === continent &&
                        item['Date of publication'] >= start &&
                        item['Date of publication'] <= end
                    ).length;
                    return count;
                }});
            }});

            const traces = Object.entries(continentData).map(([continent, counts]) => ({{
                type: 'scatter',
                mode: 'lines+markers',
                name: continent,
                x: sortedIntervals,
                y: counts,
                line: {{
                    color: continentColors[continent],
                    width: 2
                }},
                marker: {{
                    size: 8,
                    color: continentColors[continent]
                }}
            }}));

            const timelineLayout = {{
                title: {{
                    text: 'Exhibition Count by Continent',
                    font: {{ size: 14 }}
                }},
                showlegend: true,
                legend: {{
                    orientation: 'h',
                    yanchor: 'top',
                    y: -0.2,
                    xanchor: 'center',
                    x: 0.5
                }},
                margin: {{ t: 40, r: 20, l: 50, b: 100 }},
                xaxis: {{
                    title: 'Time Period',
                    tickangle: 45
                }},
                yaxis: {{
                    title: 'Number of Exhibitions'
                }},
                paper_bgcolor: 'rgba(255,255,255,0)',
                plot_bgcolor: 'rgba(255,255,255,0.5)',
                font: {{ size: 10 }},
                autosize: true
            }};

            const config = {{
                responsive: true,
                displayModeBar: false,
                scrollZoom: false
            }};

            Plotly.newPlot('timeline', traces, timelineLayout, config);
        }}

        function updateTimeline() {{
            const selectedIntervals = Array.from(
                document.querySelectorAll('#year-checkboxes input:checked')
            ).map(cb => cb.value);

            if (selectedIntervals.length === 0) {{
                Plotly.newPlot('timeline', [], {{}});
                return;
            }}

            const filteredData = originalData.filter(item => {{
                const year = item['Date of publication'];
                return selectedIntervals.some(interval => {{
                    const [start, end] = interval.split('-').map(Number);
                    return year >= start && year <= end;
                }});
            }});

            createTimelinePlot(filteredData, selectedIntervals);
        }}

        function updateMap() {{
            const selectedIntervals = Array.from(
                document.querySelectorAll('#year-checkboxes input:checked')
            ).map(cb => cb.value);

            if (selectedIntervals.length === 0) {{
                Plotly.newPlot('map', [], layout, config);
                return;
            }}

            const filteredData = originalData.filter(item => {{
                const year = item['Date of publication'];
                return selectedIntervals.some(interval => {{
                    const [start, end] = interval.split('-').map(Number);
                    return year >= start && year <= end;
                }});
            }});

            const pointTraces = createTraces(filteredData);
            const lineTraces = createPublisherLines(filteredData);
            
            Plotly.newPlot('map', [...lineTraces, ...pointTraces], layout, config);
        }}

        const layout = {{
            mapbox: {{
                style: 'satellite-streets',
                center: {{ lat: 20, lon: 0 }},
                zoom: 1.5,
                accesstoken: 'pk.eyJ1IjoieGZsaXUiLCJhIjoiY202MjRkaTBmMHgzdjJxc2JyNzZpZXZtcSJ9.zQegKx3mZRaYMj6DLjhB6Q'
            }},
            margin: {{ t: 0, b: 0, l: 0, r: 0 }},
            autosize: true,
            showlegend: false,
            hoverdistance: 5,
            hovermode: 'closest',
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            modebar: {{
                bgcolor: 'transparent'
            }}
        }};

        const config = {{
            scrollZoom: true,
            displayModeBar: true,
            displaylogo: false
        }};

        const yearCheckboxesContainer = document.getElementById('year-checkboxes');
        yearIntervals.forEach(interval => {{
            const label = document.createElement('label');
            label.className = 'year-checkbox';
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = interval;
            const text = document.createTextNode(interval);
            label.appendChild(checkbox);
            label.appendChild(text);
            yearCheckboxesContainer.appendChild(label);
            checkbox.addEventListener('change', () => {{
                updateMap();
                updateTimeline();
            }});
        }});

        document.getElementById('select-all-btn').addEventListener('click', () => {{
            document.querySelectorAll('#year-checkboxes input[type="checkbox"]')
                .forEach(cb => {{
                    cb.checked = true;
                    cb.dispatchEvent(new Event('change'));
                }});
        }});

        document.getElementById('deselect-all-btn').addEventListener('click', () => {{
            document.querySelectorAll('#year-checkboxes input[type="checkbox"]')
                .forEach(cb => {{
                    cb.checked = false;
                    cb.dispatchEvent(new Event('change'));
                }});
        }});

        window.addEventListener('resize', () => {{
            layout.height = window.innerHeight;
            layout.width = window.innerWidth;
            updateMap();
            if (document.querySelector('#timeline-container .panel-content').classList.contains('active')) {{
                requestAnimationFrame(() => {{
                    updateTimeline();
                }});
            }}
        }});

        layout.height = window.innerHeight;
        layout.width = window.innerWidth;
        updateMap();
        
        // 初始化时打开时间线面板
        document.querySelector('#timeline-container .panel-content').classList.add('active');
        updateTimeline();
    </script>
</body>
</html>
    """

    # 保存HTML文件
    with open("exhibition_map.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    return None

def main():
    """主函数"""
    file_path = r"C:\Users\debuf\Desktop\DH_PROJECT\modified_dumbraton.xlsx"
    df = load_and_process_data(file_path)
    create_interactive_map(df)
    print("Map has been generated and saved as: exhibition_map.html")

if __name__ == "__main__":
    main()