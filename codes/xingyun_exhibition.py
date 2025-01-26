import pandas as pd
import numpy as np
import re
import tomotopy as tp
from collections import defaultdict
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from matplotlib.colors import LinearSegmentedColormap

class ExhibitionAnalyzer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None
        self.processed_data = None

        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
            nltk.download('punkt')

        self.stop_words = set(stopwords.words('english'))
        custom_stops = {
            'exhibition', 'exhibits', 'exhibit', 'catalog', 'catalogue',
            'collections', 'collection', 'objects', 'object', 'works',
            'the', 'and', 'of', 'in', 'at', 'to', 'for', 'from', 'by',
            'with', 'on', 'new', 'one', 'two', 'three', 'first', 'second',
            'third', 'part', 'volume', 'series', 'edition', 'vol', 'art', 'world',
            'ancient', 'through', 'between', 'among', 'before', 'after', 'during',
            'into', 'onto', 'upon', 'within', 'without', 'museum', 'museums',
            'gallery', 'galleries','000','barbier-mueller','1500-1800','2000'
        }
        self.stop_words.update(custom_stops)

        self.compound_terms = {
            'pre-columbian': 'Pre_Columbian',
            'pre-hispanic': 'Pre_Hispanic',
            'colonial latin america': 'Colonial_Latin_America',
            'spanish america': 'Spanish_America',
            'south america': 'South_America',
            'central america': 'Central_America',
            'north america': 'North_America',
            'new spain': 'New_Spain',
            'western mexico': 'Western_Mexico',
            'costa rica': 'Costa_Rica',
            'el salvador': 'El_Salvador',
            'spanish conquest': 'Spanish_Conquest',
            'colonial peru': 'Colonial_Peru',
            'colonial andes': 'Colonial_Andes',
            'moche art': 'Moche_Art',
            'chavin culture': 'Chavin_Culture',
            'aztec empire': 'Aztec_Empire',
            'olmec world': 'Olmec_World',
        }

    def load_data(self):
        try:
            self.df = pd.read_excel(self.file_path)
        except Exception as e:
            raise
        return self
        
    def process_date_range(self, date_str):
        if pd.isna(date_str):
            return None, None
            
        date_str = str(date_str).strip()
        range_match = re.match(r'(\d{4})\s*-\s*(\d{4})', date_str)
        if range_match:
            start_year = int(range_match.group(1))
            end_year = int(range_match.group(2))
            return start_year, end_year
            
        single_year = re.match(r'(\d{4})', date_str)
        if single_year:
            year = int(single_year.group(1))
            return year, year
            
        return None, None
        
    def get_decades(self, start_year, end_year):
        if start_year is None or end_year is None:
            return []
            
        decades = []
        for year in range(start_year, end_year + 1):
            decade = (year // 10) * 10
            if decade not in decades:
                decades.append(decade)
        return decades
        
    def process_data(self):
        if self.df is None:
            raise ValueError("请先使用 load_data() 加载数据")
            
        processed_records = []
        
        for _, row in self.df.iterrows():
            start_year, end_year = self.process_date_range(row['Date of publication'])
            decades = self.get_decades(start_year, end_year)
            
            for decade in decades:
                processed_records.append({
                    'decade': decade,
                    'title': row['Title'],
                    'text': str(row['Title'])
                })
                
        self.processed_data = pd.DataFrame(processed_records)
        self.processed_data = self.processed_data.sort_values('decade')
        return self

    def preprocess_text(self, text):
        text = text.lower()
        
        for term, replacement in self.compound_terms.items():
            text = text.replace(term, replacement)
            text = text.replace(term.replace('-', ' '), replacement)
        
        text = re.sub(r'[^\w\s-]', ' ', text)
        words = word_tokenize(text)
        words = [word for word in words 
                if (word not in self.stop_words and len(word) > 2)
                or word in self.compound_terms.values()]
        
        return words

    def create_topic_model(self, num_topics=2, iterations=1000):
        if self.processed_data is None:
            raise ValueError("请先处理数据")
            
        unique_decades = sorted(self.processed_data['decade'].unique())
        time_slices = len(unique_decades)

        model = tp.DTModel(
            k=num_topics,
            t=time_slices,
            tw=tp.TermWeight.ONE,
            min_cf=2,
            min_df=2,
            rm_top=0,
            alpha_var=0.1,
            eta_var=0.1,
            phi_var=0.1,
            lr_a=0.01,
            lr_b=0.1,
            lr_c=0.55
        )
        
        decade_to_timepoint = {decade: idx for idx, decade in enumerate(unique_decades)}
        documents_per_decade = defaultdict(int)
        
        for _, doc in self.processed_data.iterrows():
            words = self.preprocess_text(doc['text'])
            if words:
                timepoint = decade_to_timepoint[doc['decade']]
                model.add_doc(words=words, timepoint=timepoint)
                documents_per_decade[doc['decade']] += 1
        
        for i in range(0, iterations, 10):
            model.train(10)
            if i % 100 == 0:
                pass
        
        return model, unique_decades, decade_to_timepoint
        
class TopicVisualizer:
    def __init__(self, model, unique_decades, decade_to_timepoint):
        self.model = model
        self.unique_decades = unique_decades
        self.decade_to_timepoint = decade_to_timepoint
        
        self.colors = [(239/255, 235/255, 221/255),
                      (210/255, 180/255, 140/255),
                      (139/255, 69/255, 19/255),
                      (101/255, 67/255, 33/255)]
        self.brown_colormap = LinearSegmentedColormap.from_list("custom_brown", self.colors)
        
    def create_wordcloud_for_decade(self, decade):
        timepoint = self.decade_to_timepoint[decade]
        word_freq = {}
        
        for topic_idx in range(self.model.k):
            topic_words = self.model.get_topic_words(topic_idx, timepoint=timepoint, top_n=30)
            for word, prob in topic_words:
                if word in word_freq:
                    word_freq[word] = max(word_freq[word], prob)
                else:
                    word_freq[word] = prob
        
        plt.figure(figsize=(15, 8))
        
        wordcloud = WordCloud(
            width=1600,
            height=800,
            background_color='#FDF5E6',
            max_words=50,
            prefer_horizontal=0.7,
            scale=3,
            colormap=self.brown_colormap,
            relative_scaling=0.5,
            min_font_size=10,
            max_font_size=120
        ).generate_from_frequencies(word_freq)
        
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        
        plt.title(f'Exhibition Themes: {decade}s', 
                 fontsize=24, 
                 pad=20, 
                 color='#8B4513', 
                 fontweight='bold')
        
        plt.savefig(f'wordcloud_{decade}s.png', 
                   dpi=300, 
                   bbox_inches='tight', 
                   facecolor='#FDF5E6',
                   edgecolor='none')
        plt.close()
        
        return wordcloud

    def create_all_wordclouds(self, min_decade=1950):
        valid_decades = [d for d in self.unique_decades if d >= min_decade]
        wordclouds = {}
        for decade in valid_decades:
            wordcloud = self.create_wordcloud_for_decade(decade)
            wordclouds[decade] = wordcloud
            
        return wordclouds

def main():
    analyzer = ExhibitionAnalyzer('/Users/sauregurkenzeit/Desktop/modified_dumbraton.xlsx')
    analyzer.load_data().process_data()
    model, unique_decades, decade_to_timepoint = analyzer.create_topic_model(
        num_topics=2,
        iterations=2000
    )
    visualizer = TopicVisualizer(model, unique_decades, decade_to_timepoint)
    wordclouds = visualizer.create_all_wordclouds(min_decade=1950)
    return analyzer, model, visualizer, wordclouds

if __name__ == "__main__":
    analyzer, model, visualizer, wordclouds = main()