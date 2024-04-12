import pandas as pd

# Reading the DataFrame from the saved CSV file
df = pd.read_csv('df.csv')

top_artists_df = pd.read_csv('top_artist.csv')

print(top_artists_df)