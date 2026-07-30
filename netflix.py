# Netflix Data Analysis
# Works in Python IDLE

import pandas as pd
import matplotlib.pyplot as plt

# Load dataset
df = pd.read_csv("netflix_titles.csv")

print("=" * 50)
print("NETFLIX DATA ANALYSIS")
print("=" * 50)

# Basic information
print("\nDataset Shape:")
print(df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nMissing Values:")
print(df.isnull().sum())

# --------------------------------------------------
# Movies By Release Year
# --------------------------------------------------

movies = df[df["type"] == "Movie"]

year_counts = movies["release_year"].value_counts().sort_index()

plt.figure(figsize=(10, 5))
year_counts.plot()
plt.title("Movies Released by Year")
plt.xlabel("Year")
plt.ylabel("Number of Movies")
plt.grid(True)
plt.show()

# --------------------------------------------------
# Top Genres
# --------------------------------------------------

genre_series = df["listed_in"].dropna()

genres = {}

for item in genre_series:
    for genre in item.split(","):
        genre = genre.strip()
        genres[genre] = genres.get(genre, 0) + 1

genre_df = pd.DataFrame(
    genres.items(),
    columns=["Genre", "Count"]
)

top_genres = genre_df.sort_values(
    by="Count",
    ascending=False
).head(10)

print("\nTop 10 Genres:")
print(top_genres)

plt.figure(figsize=(10, 5))
plt.bar(top_genres["Genre"], top_genres["Count"])
plt.title("Top 10 Netflix Genres")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# --------------------------------------------------
# Country-wise Trends
# --------------------------------------------------

country_counts = {}

for item in df["country"].dropna():
    for country in item.split(","):
        country = country.strip()
        country_counts[country] = country_counts.get(country, 0) + 1

country_df = pd.DataFrame(
    country_counts.items(),
    columns=["Country", "Count"]
)

top_countries = country_df.sort_values(
    by="Count",
    ascending=False
).head(10)

print("\nTop 10 Countries:")
print(top_countries)

plt.figure(figsize=(10, 5))
plt.bar(top_countries["Country"], top_countries["Count"])
plt.title("Top 10 Countries on Netflix")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# --------------------------------------------------
# Movie vs TV Show Distribution
# --------------------------------------------------

type_counts = df["type"].value_counts()

plt.figure(figsize=(6, 6))
plt.pie(
    type_counts,
    labels=type_counts.index,
    autopct="%1.1f%%"
)
plt.title("Movies vs TV Shows")
plt.show()

print("\nAnalysis Complete!")
