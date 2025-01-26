import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def create_exhibition_timeline(df):
    def get_period(year):
        if '-' in str(year):
            year = int(str(year).split('-')[0])
        return f"{(year // 5) * 5}-{(year // 5) * 5 + 4}"

    df['Year'] = df['Date of publication'].apply(lambda x: int(str(x).split('-')[0]) if '-' in str(x) else x)
    df['Period'] = df['Year'].apply(get_period)

    timeline_data = df.groupby(['Period', 'Continent']).size().unstack(fill_value=0)

    plt.style.use('seaborn')
    plt.figure(figsize=(15, 8), facecolor='none')
    plt.rcParams['figure.facecolor'] = 'none'
    plt.rcParams['axes.facecolor'] = 'none'

    colors = {
        'LATIN AMERICA': '#FF6B6B',
        'EUROPE': '#4ECDC4',
        'NORTH AMERICA': '#45B7D1',
        'ASIA': '#96CEB4',
        'OCEANIA': '#FFBE0B'
    }

    for continent in colors.keys():
        if continent in timeline_data.columns:
            plt.plot(range(len(timeline_data.index)),
                     timeline_data[continent],
                     marker='o',
                     label=continent,
                     color=colors[continent],
                     linewidth=2)

    plt.title('Exhibition Count by Continent', fontsize=14, pad=20, color='black')
    plt.xlabel('Time Period', fontsize=12, color='black')
    plt.ylabel('Number of Exhibitions', fontsize=12, color='black')
    plt.grid(True, alpha=0.3)

    plt.xticks(range(len(timeline_data.index)),
               timeline_data.index,
               rotation=45,
               ha='right',
               color='black')
    plt.yticks(color='black')

    plt.legend(bbox_to_anchor=(1.02, 1),
               loc='upper left')

    plt.tight_layout()
    return plt


df = pd.read_excel(r'C:\Users\debuf\Desktop\DH_PROJECT\modified_dumbraton.xlsx')
plt = create_exhibition_timeline(df)
plt.savefig('exhibition_timeline.png', transparent=True, bbox_inches='tight', dpi=300)