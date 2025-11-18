import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import itertools
from collections import Counter
import re

# --- Statistik Dasar ---

def calculate_basic_stats(series_before, series_after):
    try:
        # Hitung rata-rata panjang kata
        avg_before = series_before.astype(str).str.split().str.len().mean()
        avg_after = series_after.astype(str).str.split().str.len().mean()
        return avg_before, avg_after
    except:
        return 0, 0

# --- Perhitungan Frekuensi ---

@st.cache_data(hash_funcs={pd.Series: lambda s: "".join(s.astype(str))})
def calculate_word_frequency(data_series, is_tokenized):
    try:
        all_tokens = []
        if is_tokenized:
            # Untuk data sesudah preprocessing (List of strings)
            all_tokens = list(itertools.chain.from_iterable(data_series.dropna()))
        else:
            # Untuk data mentah (String) - Simple Regex Tokenization
            all_text = ' '.join(data_series.dropna().astype(str))
            all_tokens = re.findall(r'\b\w+\b', all_text.lower())

        if not all_tokens:
            return pd.DataFrame(columns=['Kata', 'Frekuensi'])
            
        word_counts = Counter(all_tokens)
        df_freq = pd.DataFrame(word_counts.items(), columns=['Kata', 'Frekuensi'])
        df_freq = df_freq.sort_values(by='Frekuensi', ascending=False).reset_index(drop=True)
        return df_freq
        
    except Exception as e:
        st.error(f"Error calculating frequency: {e}")
        return pd.DataFrame(columns=['Kata', 'Frekuensi'])

# --- Visualisasi (Best Practice: Return Figure Object) ---

@st.cache_data
def create_wordcloud(freq_dict):
    if not freq_dict:
        return WordCloud(width=800, height=400, background_color='white').generate("No Data")
        
    wc = WordCloud(
        width=800, height=400,
        background_color='white',
        colormap='viridis',
        max_words=150,
        random_state=42
    )
    wc.generate_from_frequencies(freq_dict)
    return wc

@st.cache_data
def plot_word_frequency_seaborn(df_freq, top_n=20):
    """Membuat bar plot menggunakan Seaborn dengan Object Oriented Interface."""
    if df_freq.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Tidak ada data", ha='center', va='center')
        return fig

    # Setup Figure dan Axes
    fig, ax = plt.subplots(figsize=(10, 7))
    
    df_top_n = df_freq.head(top_n)
    
    sns.barplot(
        x='Frekuensi',
        y='Kata',
        data=df_top_n,
        palette='viridis',
        hue='Kata',
        legend=False,
        ax=ax # Penting: Plot ke axes spesifik, bukan global plt
    )
    
    ax.set_title(f'Top {top_n} Kata Paling Sering Muncul', fontsize=16)
    ax.set_xlabel('Frekuensi', fontsize=12)
    ax.set_ylabel('Kata', fontsize=12)
    ax.grid(axis='x', linestyle='--', alpha=0.6)
    
    # Anotasi nilai
    for p in ax.patches:
        width = p.get_width()
        ax.text(
            width + 0.5,
            p.get_y() + p.get_height() / 2,
            f'{int(width)}', 
            va='center',
            fontsize=10
        )
    
    plt.tight_layout()
    return fig