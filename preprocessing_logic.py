import os
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
                pass


def get_stopword_list(language):
    if language == 'id':
        factory = StopWordRemoverFactory()
        base_stopwords = set(factory.get_stop_words())

        # PENTING: Karena Normalisasi dilakukan DULUAN, maka kata baku (seperti 'tidak')
        # harus ada di stopword list ini agar terhapus.

        # Hapus kata negasi dari stopword bawaan jika ingin analisis sentimen detil
        # Tapi jika ingin wordcloud bersih, biarkan saja.
        negation_words = {'tidak', 'tak', 'jangan', 'bukan', 'belum', 'kurang'}
        base_stopwords = base_stopwords - negation_words

        custom_stopwords = set([
            # 1. KATA GANTI & SAPAAN
            'aku', 'akuu', 'saya', 'sy', 'gw', 'gue', 'lu', 'lo', 'kamu', 'kamuu', 'kita', 'dia',
            'kak', 'kakak', 'mas', 'bro', 'sis', 'min', 'minn', 'mimin', 'gan', 'bang',
            'pak', 'bu', 'bapak', 'ibu',

            # 2. STEMMING LEAK (Kata 'jadi' dll)
            'jadi', 'menjadi', 'terjadi', 'dijadikan', 'kejadian', 'jadinya',

            # 3. KATA UMUM / SAMPAH (Noise)
            'moga', 'banget', 'bgt', 'nya', 'ya', 'yaa', 'iya', 'pas', 'dpt',
            'dn', 'ada', 'bisa', 'juga', 'doang', 'dlm', 'tapi', 'tp', 'tpi',
            'ga', 'gak', 'nggak', 'enggak', 'gaes', 'guys', 'jg', 'bln', 'ny', 'sampe',  # Pastikan ada koma
            'nih', 'tuh', 'sih', 'dong', 'deh', 'kok', 'mah', 'udh', 'sdh', 'dah',
            'yg', 'dgn', 'utk', 'karena', 'krn', 'aja', 'sja', 'lg', 'lagi',
            'smoga', 'smg', 'kyk', 'kek', 'kalo', 'kalau', 'kl',
            'mau', 'apa', 'kenapa', 'gimana', 'kapan', 'mana', 'nichh',
            'tadi', 'segini', 'begini', 'begitu', 'udah'
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
        # Gunakan nama file CSV yang benar
        file_path = 'kamuskatabaku.csv'

        # Cek apakah file ada
        if not os.path.exists(file_path):
            st.warning(f"File '{file_path}' tidak ditemukan. Normalisasi dilewati.")
            return {}

        # Baca CSV (Bukan Excel)
        df_kamus = pd.read_csv(file_path, on_bad_lines='skip')

        col_slang = 'slang' if 'slang' in df_kamus.columns else 'tidak_baku'
        col_formal = 'formal' if 'formal' in df_kamus.columns else 'kata_baku'

        if col_slang in df_kamus.columns and col_formal in df_kamus.columns:
            kamus_dict = dict(zip(df_kamus[col_slang], df_kamus[col_formal]))
            return kamus_dict
        else:
            return {}

    except Exception as e:
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
        # Hanya ambil HURUF (Angka dibuang: isalpha)
        if token.isalpha() and token != '':
            cleaned_tokens.append(token)
    return cleaned_tokens


def normalize_kata_baku(tokens, kamus_dict):
    # Mengganti token slang dengan token baku dari kamus
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

    # Load resources
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
        tokens = processed_text.split()

    teks_clean = ' '.join(tokens)
    tokens_awal = tokens[:]

    # 3. Normalization (KAMUS DULUAN)
    # Ini dijalankan sebelum Stopword removal
    if pipeline_steps.get('normalization'):
        tokens = normalize_kata_baku(tokens, kamus_dict)

    # 4. Stopword Removal (CUSTOM STOPWORD BELAKANGAN)
    if pipeline_steps.get('stopword_removal'):
        tokens = remove_stopwords(tokens, stopwords_list)

    tokens_filtered = tokens[:]

    # 5. Stemming / Lemmatization
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
    return df.to_csv(index=False).encode('utf-8')
