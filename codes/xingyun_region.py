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
import os

class RegionalExhibitionAnalyzer:
    def __init__(self, file_path, save_dir):
        self.file_path = file_path
        self.save_dir = save_dir
        self.df = None
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
            'gallery', 'galleries', '000', 'barbier-mueller', '1500-1800', '2000'
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
        self.colors = [(239/255, 235/255, 221/255),
                      (210/255, 180/255, 140/255),
                      (139/255, 69/255, 19/255),
                      (101/255, 67/255, 33/255)]
        self.brown_colormap = LinearSegmentedColormap.from_list("custom_brown", self.colors)
        os.makedirs(save_dir, exist_ok=True)

    def load_data(self):
        try:
            self.df = pd.read_excel(self.file_path)
            return self
        except Exception as e:
            raise

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

    def create_regional_distribution(self):
        region_counts = self.df['Continent'].value_counts()
        plt.figure(figsize=(12, 6))
        ax = plt.gca()
        ax.set_facecolor('none')
        plt.gcf().set_facecolor('none')
        bars = plt.barh(range(len(region_counts)), region_counts.values,
                     color=self.brown_colormap(np.linspace(0.2, 0.8, len(region_counts))),
                     alpha=0.8)
        for i, bar in enumerate(bars):
            width = bar.get_width()
            plt.text(width + 0.5, i, f'{int(width)}',
                    ha='left', va='center', color='#8B4513',
                    fontsize=12, fontweight='bold')
        plt.title('Distribution of Exhibitions by Region',
                 fontsize=24, y=1.05, color='#8B4513', fontweight='bold')
        plt.xlabel('Number of Exhibitions', fontsize=14, color='#8B4513', fontweight='bold')
        plt.yticks(range(len(region_counts)), region_counts.index,
                  color='#8B4513', fontweight='bold')
        plt.xticks(color='#8B4513', fontweight='bold')
        plt.grid(True, alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        plt.tight_layout()
        save_path = os.path.join(self.save_dir, 'regional_distribution.png')
        plt.savefig(save_path, dpi=300, bbox_inches='tight', transparent=True)
        plt.close()
        return region_counts

    def analyze_regional_themes(self, num_topics=2, min_docs=5):
        region_models = {}
        region_summaries = defaultdict(list)
        for region in self.df['Continent'].unique():
            region_texts = self.df[self.df['Continent'] == region]['Title'].tolist()
            doc_count = len(region_texts)
            if doc_count < min_docs:
                continue
            try:
                model = tp.LDAModel(
                    k=num_topics,
                    tw=tp.TermWeight.ONE,
                    min_cf=2,
                    min_df=2,
                    rm_top=0,
                    alpha=0.1,
                    eta=0.01
                )
                for text in region_texts:
                    words = self.preprocess_text(text)
                    if words:
                        model.add_doc(words)
                for _ in range(0, 1000, 10):
                    model.train(10)
                region_models[region] = model
                for topic_idx in range(num_topics):
                    topic_words = model.get_topic_words(topic_idx, top_n=10)
                    topic_summary = [word for word, _ in topic_words]
                    region_summaries[region].append(topic_summary)
            except Exception:
                continue
        return region_models, region_summaries

    def create_combined_wordcloud(self, region, model):
        word_freq = {}
        for topic_idx in range(model.k):
            topic_words = model.get_topic_words(topic_idx, top_n=30)
            for word, prob in topic_words:
                if word in word_freq:
                    word_freq[word] = max(word_freq[word], prob)
                else:
                    word_freq[word] = prob
        plt.figure(figsize=(15, 8))
        wordcloud = WordCloud(
            width=1600,
            height=800,
            background_color=None,
            mode='RGBA',
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
        plt.title(f'Exhibition Themes in {region}',
                 fontsize=24, pad=20, color='#8B4513', fontweight='bold')
        save_path = os.path.join(self.save_dir, f'wordcloud_{region}.png')
        plt.savefig(save_path, dpi=300, bbox_inches='tight', transparent=True)
        plt.close()
        return wordcloud

    def analyze_topic_similarities(self, region_models):
        similarities = []
        regions = list(region_models.keys())
        for i, region1 in enumerate(regions):
            for j, region2 in enumerate(regions[i+1:], i+1):
                region1_words = set()
                region2_words = set()
                for topic_idx in range(region_models[region1].k):
                    words = set(word for word, _ in 
                              region_models[region1].get_topic_words(topic_idx, top_n=20))
                    region1_words.update(words)
                for topic_idx in range(region_models[region2].k):
                    words = set(word for word, _ in 
                              region_models[region2].get_topic_words(topic_idx, top_n=20))
                    region2_words.update(words)
                similarity = len(region1_words & region2_words) / len(region1_words | region2_words)
                common_words = sorted(list(region1_words & region2_words))
                result = {
                    'region1': region1,
                    'region2': region2,
                    'similarity': similarity,
                    'common_words': common_words
                }
                similarities.append(result)
        return similarities

def main():
    save_dir = '/Users/sauregurkenzeit/Desktop/pic2'
    file_path = '/Users/sauregurkenzeit/Desktop/modified_dumbraton.xlsx'
    try:
        analyzer = RegionalExhibitionAnalyzer(file_path, save_dir)
        analyzer.load_data()
        region_counts = analyzer.create_regional_distribution()
        region_models, region_summaries = analyzer.analyze_regional_themes(num_topics=2)
        for region, model in region_models.items():
            analyzer.create_combined_wordcloud(region, model)
        similarities = analyzer.analyze_topic_similarities(region_models)
    except Exception:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()