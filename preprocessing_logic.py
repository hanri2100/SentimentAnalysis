import string

import nltk
import pandas as pd
import streamlit as st
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize


# --- Resources Loading (Cache) ---

@st.cache_resource
def get_sastrawi_stemmer():
    factory = StemmerFactory()
    return factory.create_stemmer()


@st.cache_resource
def get_nltk_lemmatizer():
    return WordNetLemmatizer()


def load_nltk_resources():
    resources = ['punkt', 'stopwords', 'wordnet', 'punkt_tab']
    for res in resources:
        try:
            nltk.data.find(f'tokenizers/{res}')
        except LookupError:
            try:
                nltk.download(res, quiet=True)
            except:
                pass  # Handle if download fails gracefully


def get_stopword_list(language):
    if language == 'id':
        factory = StopWordRemoverFactory()
        base_stopwords = set(factory.get_stop_words())
        negation_words = {'tidak', 'tak', 'jangan', 'bukan', 'belum', 'kurang'}
        base_stopwords = base_stopwords - negation_words
        custom_stopwords = set([
            # Kata Ganti Orang
            'aku', 'saya', 'sy', 'gw', 'gue', 'lu', 'lo', 'kamu', 'kita', 'dia',
            
            # Kata Sapaan
            'kak', 'kakak', 'bro', 'sis', 'min', 'mimin', 'gan', 'bang',
            'jadi', 'menjadi', 'terjadi', 'dijadikan', 'kejadian', 'jadinya',
            # Kata Sambung & Keterangan Gaul
            'moga', 'banget', 'bgt', 'nya', 'ya', 'yaa', 'iya', 'pas', 'dpt',
            'dn', 'ada', 'bisa', 'juga', 'doang', 'dlm', 'tapi', 'tp', 'tpi'
            'ga', 'gak', 'nggak', 'gaes', 'guys', 'jg', 'bln', 'ny', 'sampe',
            'nih', 'tuh', 'sih', 'dong', 'deh', 'kok', 'mah', 'ny', 'udh',
            'yg', 'dgn', 'utk', 'karena', 'krn', 'aja', 'sja', 'lg', 'lagi',
            'smoga', 'smg', 'jg', 'jga', 'kyk', 'kek', 'kalo', 'kalau', 'kl',
            'mau', 'apa', 'kenapa', 'gimana', 'kapan', 'mana',
            'pas', 'tadi', 'segini', 'begini', 'begitu', 'udh', 'udah', 'dah',
            'telkom', 'university', 'univ', 'kampus', 'tel-u'
        ])
        return base_stopwords.union(custom_stopwords)
    elif language == 'en':
        try:
            return set(stopwords.words('english'))
        except:
            return set()
    return set()


@st.cache_data
def load_kamus_kata_baku():
    try:
        # Pastikan file ada, jika tidak return dict kosong
        df_kamus = pd.read_excel('/kamuskatabaku.xlsx')
        col_slang = 'slang' if 'slang' in df_kamus.columns else 'tidak_baku'
        col_formal = 'formal' if 'formal' in df_kamus.columns else 'kata_baku'

        kamus_dict = dict(zip(df_kamus[col_slang], df_kamus[col_formal]))
        return kamus_dict

    except Exception as e:
        # Tampilkan error agar kita tahu apa salahnya
        st.error(f"Error Loading Kamus: {e}")
        return {}


# --- Text Processing Functions ---

def case_fold(text):
    return text.lower()


def tokenize(text):
    return word_tokenize(text)


def clean_tokens(tokens):
    cleaned_tokens = []
    for token in tokens:
        # Hapus punctuation
        token = token.translate(str.maketrans('', '', string.punctuation))
        # Pastikan alphanumeric dan tidak kosong
        if token.isalpha() and token != '':
            cleaned_tokens.append(token)
    return cleaned_tokens


def normalize_kata_baku(tokens, kamus_dict):
    return [kamus_dict.get(token, token) for token in tokens]


def remove_stopwords(tokens, stopwords_list):
    return [word for word in tokens if word not in stopwords_list]


def stem_text(tokens, stemmer):
    if not tokens: return []
    text_to_stem = ' '.join(tokens)
    return stemmer.stem(text_to_stem).split()


def lemmatize_text(tokens, lemmatizer):
    return [lemmatizer.lemmatize(word) for word in tokens]


# --- Main Pipeline ---

def preprocess_pipeline(text, pipeline_steps, language):
    if not isinstance(text, str):
        return "", [], [], [], ""

    processed_text = text

    # Load resources on the fly based on need (cached)
    stemmer = get_sastrawi_stemmer() if (language == 'id' and pipeline_steps.get('stemming')) else None
    lemmatizer = get_nltk_lemmatizer() if (language == 'en' and pipeline_steps.get('lemmatization')) else None
    stopwords_list = get_stopword_list(language) if pipeline_steps.get('stopword_removal') else set()
    kamus_dict = load_kamus_kata_baku() if pipeline_steps.get('normalization') else {}

    # 1. Case Folding
    if pipeline_steps.get('case_folding'):
        processed_text = case_fold(processed_text)

    # 2. Tokenization & Cleaning
    if pipeline_steps.get('tokenization'):
        tokens = tokenize(processed_text)
        tokens = clean_tokens(tokens)
    else:
        # Basic split if no tokenization selected (rare case)
        tokens = processed_text.split()

    teks_clean = ' '.join(tokens)
    tokens_awal = tokens[:]

    # 3. Normalization
    if pipeline_steps.get('normalization'):
        tokens = normalize_kata_baku(tokens, kamus_dict)

    # 4. Stopword Removal
    if pipeline_steps.get('stopword_removal'):
        tokens = remove_stopwords(tokens, stopwords_list)

    tokens_filtered = tokens[:]

    # 5. Stemming Bila bahasa Indonesia atau Lemmatization Bila bahasa Inggris
    if language == 'id' and pipeline_steps.get('stemming'):
        tokens = stem_text(tokens, stemmer)
    elif language == 'en' and pipeline_steps.get('lemmatization'):
        tokens = lemmatize_text(tokens, lemmatizer)

    tokens_stemmed = tokens
    teks_final_joined = ' '.join(tokens_stemmed)

    return (teks_clean, tokens_awal, tokens_filtered, tokens_stemmed, teks_final_joined)


# --- Utility Functions ---

@st.cache_data
def convert_df_to_csv(df):
    """Mengubah DataFrame menjadi format CSV binary untuk download."""
    return df.to_csv(index=False).encode('utf-8')
