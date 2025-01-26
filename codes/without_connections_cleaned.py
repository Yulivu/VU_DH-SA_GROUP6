import pandas as pd
import plotly.graph_objects as go
import json


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
    fig = go.Figure()
    grouped = df.groupby(['Latitude', 'Longitude'])

    for (lat, lon), group in grouped:
        count = len(group)
        hover_text = ["<b>Total Exhibitions:</b> " + str(count),
                      "<b>Exhibition Details:</b>"]

        for _, row in group.iterrows():
            title = row['Title']
            date = str(row['Date of publication'])
            publisher = str(row['Publisher'])
            exhibition_info = f"- {title}->{publisher} ({date})"
            hover_text.append(exhibition_info)

        hover_text = "<br>".join(hover_text)
        color = f'rgb({max(0, 255 - count * 10)}, 0, 0)'

        fig.add_trace(go.Scattergeo(
            lon=[lon],
            lat=[lat],
            mode='markers',
            marker=dict(
                size=12,
                color=color,
                opacity=0.8,
                line=dict(
                    color='white',
                    width=1
                )
            ),
            text=[hover_text],
            hoverinfo='text',
            hoverlabel=dict(
                bgcolor="white",
                font_size=13,
                font_family="Courier New, monospace",
                align="left"
            ),
            hovertemplate="%{text}<extra></extra>"
        ))

    data_json = df.to_json(orient='records')
    year_intervals_json = json.dumps(year_intervals)
    html_content = f"""
<!DOCTYPE html>
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

        const layout = {{
            geo: {{
                scope: 'world',
                showland: true,
                landcolor: 'rgb(250, 250, 250)',
                showocean: true,
                oceancolor: 'rgb(230, 230, 255)',
                showcountries: true,
                countrycolor: 'rgb(200, 200, 200)',
                showframe: false,
                projection: {{
                    type: 'equirectangular'
                }},
                lonaxis: {{
                    range: [-180, 180]
                }},
                lataxis: {{
                    range: [-90, 90]
                }}
            }},
            margin: {{ t: 0, b: 0, l: 0, r: 0 }},
            autosize: true,
            showlegend: false,
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            dragmode: 'pan'
        }};

        const config = {{
            scrollZoom: true,
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['lasso2d']
        }};

        // 切换下拉菜单
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
            checkbox.checked = true;  // 默认选中

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
                    type: 'scattergeo',
                    lon: [lon],
                    lat: [lat],
                    mode: 'markers',
                    marker: {{
                        size: 12,
                        color: `rgb(${{Math.max(0, 255 - count*10)}}, 0, 0)`,
                        opacity: 0.8,
                        line: {{
                            color: 'white',
                            width: 1
                        }}
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

        function updateMap() {{
            const selectedIntervals = Array.from(
                document.querySelectorAll('#year-checkboxes input:checked')
            ).map(cb => cb.value);

            const currentLayout = {{
                ...layout,
                width: window.innerWidth,
                height: window.innerHeight
            }};

            if (selectedIntervals.length === 0) {{
                Plotly.newPlot('map', [], currentLayout, config);
                return;
            }}

            const filteredData = originalData.filter(item => {{
                const year = item['Date of publication'];
                return selectedIntervals.some(interval => {{
                    const [start, end] = interval.split('-').map(Number);
                    return year >= start && year <= end;
                }});
            }});

            const traces = createTraces(filteredData);
            Plotly.newPlot('map', traces, currentLayout, config);
        }}

        window.addEventListener('resize', () => {{
            const currentLayout = {{
                ...layout,
                width: window.innerWidth,
                height: window.innerHeight
            }};

            const traces = createTraces(originalData);
            Plotly.newPlot('map', traces, currentLayout, config);
        }});

        layout.width = window.innerWidth;
        layout.height = window.innerHeight;
        const initialTraces = createTraces(originalData);
        Plotly.newPlot('map', initialTraces, layout, config);
    </script>
</body>
</html>
    """

    with open("exhibition_map.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    return fig


def main():
    file_path = r"C:\Users\debuf\Desktop\DH_PROJECT\modified_dumbraton.xlsx"
    df = load_and_process_data(file_path)
    create_interactive_map(df)
    print("Map saved to: exhibition_map.html")


if __name__ == "__main__":
    main()