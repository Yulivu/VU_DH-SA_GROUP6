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
    data_json = df.to_json(orient='records')
    year_intervals_json = json.dumps(year_intervals)
    color_mapping_json = json.dumps(publisher_colors)

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
        #filter-container {{ 
            position: fixed; 
            bottom: 20px; 
            left: 20px;
            z-index: 1000;
            width: 300px;
        }}
        .filter-dropdown {{ 
            background: rgba(255, 255, 255, 0.9); 
            border-radius: 10px; 
            padding: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .filter-header {{ 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            cursor: pointer;
            padding: 10px;
            font-weight: bold;
        }}
        .filter-content {{ 
            display: none;
            padding: 10px;
        }}
        .filter-content.active {{ 
            display: block; 
        }}
        .year-checkbox-grid {{ 
            display: grid; 
            grid-template-columns: repeat(4, 1fr); 
            gap: 5px;
        }}
        .year-checkbox {{ 
            display: flex; 
            align-items: center;
            font-size: 12px;
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
        }}
    </style>
</head>
<body>
    <div class="title-container">
        <h1 class="title-text">Global Exhibition Network of Indigenous Latin American Art</h1>
    </div>

    <div id="map"></div>

    <div id="filter-container">
        <div class="filter-dropdown">
            <div class="filter-header">
                Filter by Years ▼
            </div>
            <div class="filter-content">
                <div class="filter-buttons">
                    <button id="select-all-btn" class="filter-btn">Select All</button>
                    <button id="deselect-all-btn" class="filter-btn">Deselect All</button>
                </div>
                <div id="year-checkboxes" class="year-checkbox-grid"></div>
            </div>
        </div>
    </div>

    <script>
        const originalData = {data_json};
        const yearIntervals = {year_intervals_json};
        const publisherColors = {color_mapping_json};

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

        const filterHeader = document.querySelector('.filter-header');
        const filterContent = document.querySelector('.filter-content');
        filterHeader.addEventListener('click', () => {{
            filterContent.classList.toggle('active');
            filterHeader.innerHTML = filterContent.classList.contains('active') 
                ? 'Filter by Years ▲' 
                : 'Filter by Years ▼';
        }});

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
            checkbox.addEventListener('change', updateMap);
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

        window.addEventListener('resize', () => {{
            layout.height = window.innerHeight;
            layout.width = window.innerWidth;
            updateMap();
        }});

        layout.height = window.innerHeight;
        layout.width = window.innerWidth;
        updateMap();
    </script>
</body>
</html>
    """

    with open("exhibition_map.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    return None



def main():
    file_path = r"C:\Users\debuf\Desktop\DH_PROJECT\modified_dumbraton.xlsx"
    df = load_and_process_data(file_path)
    create_interactive_map(df)
    print("Map has been generated and saved as: exhibition_map.html")

if __name__ == "__main__":
    main()