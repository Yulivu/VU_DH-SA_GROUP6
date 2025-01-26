import pandas as pd
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from umap import UMAP
from hdbscan import HDBSCAN
import plotly.graph_objects as go
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
import openai
from bertopic.representation import OpenAI
from bertopic.representation import MaximalMarginalRelevance, OpenAI, KeyBERTInspired
from nltk.corpus import stopwords
import nltk

MAYA_COLORS = [
    '#C04000',  
    '#006666',  
    '#00688B',  
    '#DAA520',  
    '#8B0000',  
    '#008B8B',  
    '#4A0404',  
    '#CD853F',  
    '#191970',  
    '#B8860B',  
    '#800000',  
    '#006400',  
]

class ExhibitionBERTAnalyzer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None
        self.model = None
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.custom_stops = set(stopwords.words('english'))
        self.custom_stops.update({
            'collection', 'collections', '1821', '3000',"2000",'1600','de','western',"arts","museum","1800",
            'exhibition', 'exhibitions', 'ancient', 'artifacts',"pre",
            'objects', 'art', 'works','000','el','three','1500'
        })

        
    def load_and_preprocess(self):
        print("\nLoading and preprocessing data...")
        self.df = pd.read_excel(self.file_path)
        
        def extract_year(date_str):
            if pd.isna(date_str):
                return None
            date_str = str(date_str).strip()
            if '-' in date_str:
                years = date_str.split('-')
                return int(years[-1])
            try:
                return int(date_str)
            except ValueError:
                return None
        
        self.df['Year'] = self.df['Date of publication'].apply(extract_year)
        self.df = self.df.dropna(subset=['Year'])
        print(f"Processed {len(self.df)} exhibitions with valid dates")
        return self
        
    def create_topic_model(self):
        print("\nCreating topic model...")

        vectorizer_model = CountVectorizer(
            stop_words=list(self.custom_stops),
            min_df=2
        )

        representation_model = MaximalMarginalRelevance(diversity=0.6)

        self.model = BERTopic(  
            n_gram_range=(1, 4), 
            embedding_model=self.embedding_model,
            umap_model=UMAP(n_neighbors=15, n_components=2, min_dist=0.00, metric='cosine'),
            hdbscan_model=HDBSCAN(
                min_cluster_size=8,
                metric='manhattan',
                cluster_selection_method='eom',
                prediction_data=True
            ),
            vectorizer_model=vectorizer_model,
            verbose=True,
            representation_model = representation_model
        )
        
        documents = self.df['Title'].tolist()
        embeddings = self.embedding_model.encode(documents, show_progress_bar=True)
        topics, probs = self.model.fit_transform(documents, embeddings)
        
        print("\nCluster Analysis:")
        for topic_id in sorted(set(topics)):
            topic_docs = [doc for doc, t in zip(documents, topics) if t == topic_id]
            print(f"\nTopic {topic_id} ({len(topic_docs)} documents):")
            print("Top Words:", self.model.get_topic(topic_id))
            print("Sample Documents:")
            for doc in topic_docs[:5]:
                print(f"- {doc}")
   
        topic_info = self.model.get_topic_info()
        print("\nIdentified Topics:")
        for _, row in topic_info.iterrows():
            print(f"Topic {row['Topic']}: {row['Name']} (Size: {row['Count']})")
        
        return self
    
    def analyze_temporal_evolution(self):
        min_year = self.df['Year'].min()
        max_year = self.df['Year'].max()
        start_decade = (min_year // 10) * 10
        end_decade = (max_year // 10) * 10
        
        print(f"\nAnalyzing exhibition themes evolution from {start_decade}s to {end_decade}s")
        
        mask = (self.df['Year'] >= start_decade) & (self.df['Year'] <= end_decade + 9)
        filtered_df = self.df[mask]
        
        texts = filtered_df['Title'].tolist()
        timestamps = filtered_df['Year'].tolist()
        topics, _ = self.model.transform(texts)
        
        df_data = pd.DataFrame({
            'text': texts,
            'year': timestamps,
            'topic': topics
        })
        df_data['decade'] = df_data['year'].apply(lambda x: x - (x % 10))
        
        topics_over_time = {
            'Decade': [],
            'Topic': [],
            'Prevalence': [],
            'Name': []
        }
        
        topic_info = self.model.get_topic_info()
        topic_names = {row['Topic']: f"Topic {row['Topic']}: {row['Name']}" 
                      for _, row in topic_info.iterrows()}
        
        print("\nDecade-by-Decade Theme Analysis:")
        for decade in range(start_decade, end_decade + 10, 10):
            decade_data = df_data[df_data['decade'] == decade]
            if len(decade_data) > 0:
                topic_counts = decade_data['topic'].value_counts()
                total = len(decade_data)
                print(f"\n{decade}s ({total} exhibitions):")
                for topic, count in topic_counts.items():
                    percentage = (count / total) * 100
                    topic_name = topic_names.get(topic, f"Topic {topic}")
                    print(f"  {topic_name}: {percentage:.1f}% ({count} exhibitions)")
                    
                    topics_over_time['Decade'].append(decade)
                    topics_over_time['Topic'].append(topic)
                    topics_over_time['Prevalence'].append(percentage)
                    topics_over_time['Name'].append(topic_name)
        
        return pd.DataFrame(topics_over_time)
        
    def analyze_regional_differences(self):
        print("\nAnalyzing regional distribution of exhibition themes...")
        
        mask = self.df['Continent'].notna()
        filtered_df = self.df[mask]
        
        region_topics = {}
        topic_info = self.model.get_topic_info()
        topic_names = {row['Topic']: row['Name'] for _, row in topic_info.iterrows()}
        
        for region in filtered_df['Continent'].unique():
            region_df = filtered_df[filtered_df['Continent'] == region]
            texts = region_df['Title'].tolist()
            topics, _ = self.model.transform(texts)
            
            topic_counts = pd.Series(topics).value_counts()
            total = len(topics)
            
            region_topics[region] = {
                'total_exhibitions': total,
                'topic_distribution': {
                    topic: (count / total) * 100 
                    for topic, count in topic_counts.items()
                }
            }
            
            print(f"\n{region} ({total} exhibitions):")
            for topic, percentage in sorted(region_topics[region]['topic_distribution'].items()):
                if percentage > 0:
                    print(f"  Topic {topic} ({topic_names.get(topic, 'Unnamed')}): {percentage:.1f}%")
        
        return region_topics
        
    def visualize_temporal_evolution(self, topics_over_time_df):
        print("\nGenerating temporal evolution visualization...")
        fig = go.Figure()
        
        for idx, topic in enumerate(sorted(topics_over_time_df['Topic'].unique())):
            topic_data = topics_over_time_df[topics_over_time_df['Topic'] == topic]
            topic_name = topic_data['Name'].iloc[0].split(':', 1)[-1].strip() 
            
            color = MAYA_COLORS[idx % len(MAYA_COLORS)]
            
            fig.add_trace(go.Scatter(
                x=topic_data['Decade'],
                y=topic_data['Prevalence'],
                name=topic_name,
                mode='lines+markers',
                line=dict(width=2, color=color),
                marker=dict(size=8, color=color),
                hovertemplate="<b>%{text}</b><br>" +
                            "Decade: %{x}s<br>" +
                            "Prevalence: %{y:.1f}%<extra></extra>",
                text=[topic_name] * len(topic_data)
            ))

        fig.update_layout(
            template="plotly_white",
            title=dict(
                text="Evolution of Exhibition Themes by Decade",
                x=0.5,
                y=0.95,
                font=dict(size=20, color='#C04000')
            ),
            xaxis=dict(
                title_text="Decade",
                title_font=dict(color='#C04000'),
                tickmode='array',
                ticktext=[f'{d}s' for d in sorted(topics_over_time_df['Decade'].unique())],
                tickvals=sorted(topics_over_time_df['Decade'].unique()),
                showgrid=True,
                gridcolor='rgba(192, 64, 0, 0.1)',
                tickfont=dict(color='#C04000')
            ),
            yaxis=dict(
                title_text="Topic Prevalence (%)",
                title_font=dict(color='#C04000'),
                showgrid=True,
                gridcolor='rgba(192, 64, 0, 0.1)',
                tickfont=dict(color='#C04000')
            ),
            showlegend=True,
            legend=dict(
                font=dict(color='#C04000'),
                bgcolor='rgba(255, 255, 255, 0.9)',
                bordercolor='rgba(192, 64, 0, 0.3)',
                borderwidth=1
            ),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        fig.update_layout(margin=dict(t=100, b=100))
        fig.write_html("/Users/sauregurkenzeit/Desktop/temporal_evolution.html")
        print("Temporal evolution visualization saved as 'temporal_evolution.html'")
        return fig
        
    def visualize_regional_differences(self, region_topics):
        print("\nGenerating regional distribution visualization...")
        topic_info = self.model.get_topic_info()
        
        all_topics = set()
        for region_data in region_topics.values():
            all_topics.update(region_data['topic_distribution'].keys())
        all_topics = sorted(list(all_topics))
        
        regions = list(region_topics.keys())
        z_data = []
        for region in regions:
            row = []
            for topic in all_topics:
                percentage = region_topics[region]['topic_distribution'].get(topic, 0)
                row.append(percentage)
            z_data.append(row)
        
        topic_labels = [topic_info.loc[topic_info['Topic'] == t, 'Name'].iloc[0].split(':', 1)[-1].strip() 
               for t in all_topics]
        
        fig = go.Figure(data=go.Heatmap(
            z=z_data,
            x=topic_labels,
            y=regions,
            colorscale=[
                [0, '#FFFFFF'],
                [0.2, MAYA_COLORS[1]],  
                [0.4, MAYA_COLORS[2]],  
                [0.6, MAYA_COLORS[3]], 
                [0.8, MAYA_COLORS[4]], 
                [1, MAYA_COLORS[0]]    
            ],
            text=[[f"{val:.1f}%" for val in row] for row in z_data],
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False,
            hovertemplate="Region: %{y}<br>%{x}<br>Prevalence: %{z:.1f}%<extra></extra>"
        ))
        
        fig.update_layout(
            title=dict(
                text="Regional Distribution of Exhibition Themes",
                x=0.5,
                y=0.95,
                font=dict(size=20, color='#C04000')
            ),
            xaxis=dict(
                title="Topics",
                title_font=dict(color='#C04000'),
                tickangle=45,
                tickfont=dict(color='#C04000')
            ),
            yaxis=dict(
                title="Region",
                title_font=dict(color='#C04000'),
                tickfont=dict(color='#C04000')
            ),
            template="plotly_white",
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=800,
            width=1500,
            margin=dict(t=100, b=200)
        )

        fig.write_html("/Users/sauregurkenzeit/Desktop/regional_differences.html")
        print("Regional distribution visualization saved as 'regional_differences.html'")
        return fig

def main():
    print("\nStarting Exhibition Theme Analysis")
    print("==================================")
    
    analyzer = ExhibitionBERTAnalyzer('/Users/sauregurkenzeit/Desktop/proj/modified_dumbraton.xlsx')
    analyzer.load_and_preprocess()
    analyzer.create_topic_model()
    
    topics_over_time = analyzer.analyze_temporal_evolution()
    temporal_viz = analyzer.visualize_temporal_evolution(topics_over_time)
    
    region_topics = analyzer.analyze_regional_differences()
    regional_viz = analyzer.visualize_regional_differences(region_topics)
    
    print("\nAnalysis Complete")
    print("================")
    print("1. Temporal Evolution: The visualization shows how exhibition themes have evolved over decades.")
    print("   - Each line represents a topic's prevalence over time")
    print("   - The y-axis shows the percentage of exhibitions featuring each theme")
    print("   - Interactive visualization saved as 'temporal_evolution.html'")
    
    print("\n2. Regional Distribution: The heatmap shows how themes vary across different regions.")
    print("   - Color gradient from white to terracotta shows theme prevalence")
    print("   - Percentages show exact theme representation in each region")
    print("   - Interactive visualization saved as 'regional_differences.html'")
    
    return analyzer, topics_over_time, region_topics

if __name__ == "__main__":
    analyzer, topics_over_time, region_topics = main()