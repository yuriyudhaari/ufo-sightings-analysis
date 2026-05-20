"""
Phase C: Text mining on UFO sighting comments.
Produces:
- word_frequencies.csv          top words overall
- tfidf_by_shape.csv            distinctive words per shape family
- topic_terms.csv               LDA topic model word loadings
- topic_assignments.csv         per-document topic assignment (sampled)
- topic_by_decade.csv           topic prevalence over time
"""

import re
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation

RNG = 42

df = pd.read_csv("ufo_clean.csv", low_memory=False)
print(f"Loaded {len(df):,} reports.\n")

#Domain-specific stopwords. Standard English stopwords plus
#uninformative UFO-corpus terms.
CUSTOM_STOPWORDS = set("""
a about above after again against all am an and any are aren as at be
because been before being below between both but by could did do does
doing don down during each few for from further had has have having he
her here hers herself him himself his how i if in into is it its itself
just me more most my myself no nor not now of off on once only or other
our ours ourselves out over own same she should so some such than that
the their theirs them themselves then there these they this those
through to too under until up very was we were what when where which
while who whom why will with you your yours yourself yourselves
would also like get got see seen saw look looked looking would could
one two three four five six seven eight nine ten time times back
went came going around went thing things something anything
ufo ufos object objects sighting witness report nuforc pd note us
http www com html
""".split())


def tokenize(text):
    """Basic tokenizer for comments. Lowercase, alpha only, length >= 3."""
    if not isinstance(text, str):
        return []
    text = text.lower()
    tokens = re.findall(r"[a-z]+", text)
    return [t for t in tokens if len(t) >= 3 and t not in CUSTOM_STOPWORDS]


#Use only reports with non-trivial comments.
mask = df["comments_clean"].fillna("").str.len() >= 20
docs = df.loc[mask].copy()
print(f"Reports with usable comments: {len(docs):,} ({len(docs)/len(df):.1%})\n")

#1. Overall word frequency
cv = CountVectorizer(
    tokenizer=tokenize, lowercase=False, min_df=20,
    token_pattern=None,
)
X = cv.fit_transform(docs["comments_clean"].fillna(""))
freqs = pd.DataFrame({
    "word": cv.get_feature_names_out(),
    "count": np.asarray(X.sum(axis=0)).ravel(),
}).sort_values("count", ascending=False)
freqs.head(200).to_csv("powerbi_data/word_frequencies.csv", index=False)
print("Top 15 words overall:")
for _, r in freqs.head(15).iterrows():
    print(f"  {r['word']:18s} {int(r['count']):,}")
print()

#2. TF-IDF distinctive words by shape family
shape_docs = (
    docs.groupby("shape_family")["comments_clean"]
    .apply(lambda s: " ".join(s.fillna("")))
    .reset_index()
)
tfidf = TfidfVectorizer(
    tokenizer=tokenize, lowercase=False, min_df=2,
    max_df=0.95, token_pattern=None, max_features=2000,
)
T = tfidf.fit_transform(shape_docs["comments_clean"])
vocab = tfidf.get_feature_names_out()

tfidf_rows = []
for i, family in enumerate(shape_docs["shape_family"]):
    row = T[i].toarray().ravel()
    top_idx = row.argsort()[::-1][:15]
    for rank, idx in enumerate(top_idx, 1):
        tfidf_rows.append({
            "shape_family": family,
            "rank": rank,
            "word": vocab[idx],
            "tfidf_score": float(row[idx]),
        })
tfidf_df = pd.DataFrame(tfidf_rows)
tfidf_df.to_csv("powerbi_data/tfidf_by_shape.csv", index=False)

print("Most distinctive words per shape family (top 5):")
for family in shape_docs["shape_family"]:
    top = tfidf_df[tfidf_df["shape_family"] == family].head(5)["word"].tolist()
    print(f"  {family:18s} -> {', '.join(top)}")
print()

#3. LDA topic modeling
#Subsample for speed and to balance the corpus by year (avoid 2000s dominating).
N_TOPICS = 8
sample_per_year = (
    docs.groupby("year", group_keys=False)
    .apply(lambda g: g.sample(min(len(g), 500), random_state=RNG))
)
print(f"LDA training sample: {len(sample_per_year):,} reports\n")

cv_lda = CountVectorizer(
    tokenizer=tokenize, lowercase=False,
    min_df=20, max_df=0.6, token_pattern=None, max_features=3000,
)
X_lda = cv_lda.fit_transform(sample_per_year["comments_clean"].fillna(""))
print(f"Vocabulary size: {len(cv_lda.get_feature_names_out())}")

lda = LatentDirichletAllocation(
    n_components=N_TOPICS,
    learning_method="online",
    random_state=RNG,
    n_jobs=-1,
    max_iter=20,
)
lda.fit(X_lda)
print("LDA model trained.\n")

# Top words per topic.
vocab_lda = cv_lda.get_feature_names_out()
topic_rows = []
for topic_idx, topic in enumerate(lda.components_):
    top = topic.argsort()[::-1][:15]
    for rank, word_idx in enumerate(top, 1):
        topic_rows.append({
            "topic_id": topic_idx,
            "rank": rank,
            "word": vocab_lda[word_idx],
            "loading": float(topic[word_idx]),
        })
topic_terms = pd.DataFrame(topic_rows)
topic_terms.to_csv("powerbi_data/topic_terms.csv", index=False)

print("LDA topics — top 8 words each:")
for topic_idx in range(N_TOPICS):
    top = topic_terms[topic_terms["topic_id"] == topic_idx].head(8)["word"].tolist()
    print(f"  Topic {topic_idx}: {', '.join(top)}")
print()

#Topic assignments for the full corpus (to enable topic-over-time analysis).
X_full = cv_lda.transform(docs["comments_clean"].fillna(""))
topic_distrib = lda.transform(X_full)
docs["dominant_topic"] = topic_distrib.argmax(axis=1)
docs["topic_score"] = topic_distrib.max(axis=1)

#Export a slim per-document table.
topic_assign = docs[["sighting_dt", "year", "decade", "shape_family",
                     "country", "state", "dominant_topic", "topic_score"]].copy()
topic_assign.to_csv("powerbi_data/topic_assignments.csv", index=False)

#Topic prevalence by decade.
topic_decade = (
    docs.dropna(subset=["decade"])
    .groupby(["decade", "dominant_topic"])
    .size()
    .reset_index(name="reports")
)
topic_decade["decade_total"] = topic_decade.groupby("decade")["reports"].transform("sum")
topic_decade["share"] = topic_decade["reports"] / topic_decade["decade_total"]
topic_decade["decade"] = topic_decade["decade"].astype(int)
topic_decade.to_csv("powerbi_data/topic_by_decade.csv", index=False)

print("Topic prevalence in 2000s:")
mix = topic_decade[topic_decade["decade"] == 2000].sort_values("share", ascending=False)
for _, r in mix.iterrows():
    top_words = topic_terms[topic_terms["topic_id"] == r["dominant_topic"]].head(3)["word"].tolist()
    print(f"  Topic {int(r['dominant_topic'])} ({', '.join(top_words)}): {r['share']:.1%}")

print("\nAll Phase C outputs saved to powerbi_data/")