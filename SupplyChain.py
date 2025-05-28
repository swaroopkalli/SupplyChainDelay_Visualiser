import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
import math
import folium
from folium.plugins import HeatMap # For density-based shading
import branca.colormap as cm # Kept, though not used in the final map type, good for other color scales if needed

# Load the CSV file
file_path = 'supply_chain_data.csv'
df = pd.read_csv(file_path)

# Drop null values
df.dropna(inplace=True)

# Select numerical and categorical columns
numerical_cols = df.select_dtypes(include=['int64', 'float64']).columns
categorical_cols = df.select_dtypes(include=['object', 'category']).columns

# Initialize PDF
pdf = PdfPages("supply_chain_analysis_graphs.pdf")

# --- Box Plot ---
plt.figure(figsize=(12, 6))
sns.boxplot(data=df[numerical_cols])
plt.xticks(rotation=90)
plt.title("Box Plot of Numerical Features")
plt.tight_layout()
pdf.savefig()
plt.close()

# --- Histogram ---
cols = 4
rows = math.ceil(len(numerical_cols) / cols)
fig, axs = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
axs = axs.flatten()
for i, col in enumerate(numerical_cols):
    df[col].hist(ax=axs[i], bins=15, edgecolor='black')
    axs[i].set_title(f'Histogram of {col}')
for j in range(i + 1, len(axs)):
    axs[j].axis('off')
plt.tight_layout()
pdf.savefig()
plt.close()

# --- KDE Plots (Added) ---
# Kernel Density Estimate plots for numerical distributions
cols = 4
rows = math.ceil(len(numerical_cols) / cols)
fig, axs = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
axs = axs.flatten()
for i, col in enumerate(numerical_cols):
    sns.kdeplot(df[col], ax=axs[i], fill=True)
    axs[i].set_title(f'KDE of {col}')
for j in range(i + 1, len(axs)):
    axs[j].axis('off')
plt.tight_layout()
pdf.savefig()
plt.close()


# --- Line Plot (Revenue Generated) ---
if 'Revenue generated' in df.columns:
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=df['Revenue generated'])
    plt.title("Line Plot of Revenue Generated")
    plt.xlabel("Index")
    plt.ylabel("Revenue")
    plt.tight_layout()
    pdf.savefig()
    plt.close()

# --- Correlation Heatmap ---
plt.figure(figsize=(12, 10))
corr = df[numerical_cols].corr()
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm")
plt.title("Correlation Heatmap")
plt.tight_layout()
pdf.savefig()
plt.close()

# --- Violin Plot (added with Product type and Defect rates) ---
# Using 'Product type' as the categorical column and 'Defect rates' as the numerical column.
if 'Product type' in df.columns and 'Defect rates' in df.columns:
    plt.figure(figsize=(10, 6))
    sns.violinplot(x='Product type', y='Defect rates', data=df)
    plt.title("Violin Plot of Defect Rates by Product Type")
    plt.xticks(rotation=45, ha='right') # Rotate labels for better readability
    plt.tight_layout()
    pdf.savefig()
    plt.close()
else:
    print("Skipping Violin Plot: 'Product type' or 'Defect rates' columns not found.")


# --- Frequency Counts (Categorical Columns) ---
for col in categorical_cols:
    plt.figure(figsize=(10, 5))
    df[col].value_counts().head(10).plot(kind='bar')
    plt.title(f'Frequency Count of {col} (Top 10)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    pdf.savefig()
    plt.close()

# --- Scatter Plots (Top correlated pairs) ---
top_pairs = corr.abs().unstack().sort_values(kind="quicksort", ascending=False)
seen = set()
count = 0
for (col1, col2) in top_pairs.index:
    if col1 != col2 and (col2, col1) not in seen:
        plt.figure(figsize=(8, 6))
        sns.scatterplot(x=df[col1], y=df[col2])
        plt.title(f"Scatter Plot: {col1} vs {col2}")
        plt.tight_layout()
        pdf.savefig()
        plt.close()
        seen.add((col1, col2))
        count += 1
        if count >= 5:  # Limit to top 5 pairs
            break

# --- Pairplot 
sns.pairplot(df[numerical_cols].sample(n=min(500, len(df)) if len(df) > 1 else 1)) # Sample up to 500 rows for performance
pdf.savefig()
plt.close()


# --- Grouped Analysis ---
grouping_cols = ['Shipping mode', 'Product category', 'Customer segment']
for col in grouping_cols:
    if col in df.columns:
        plt.figure(figsize=(10, 6))
        df.groupby(col)['Revenue generated'].mean().sort_values().plot(kind='bar')
        plt.title(f"Average Revenue by {col}")
        plt.xticks(rotation=45)
        plt.ylabel("Average Revenue")
        plt.tight_layout()
        pdf.savefig()
        plt.close()

# --- Bar Charts for Summary Stats ---
if 'Region' in df.columns and 'Revenue generated' in df.columns:
    plt.figure(figsize=(10, 6))
    df.groupby('Region')['Revenue generated'].sum().sort_values().plot(kind='bar')
    plt.title("Total Revenue by Region")
    plt.ylabel("Total Revenue")
    plt.tight_layout()
    pdf.savefig()
    plt.close()

# --- Key Trend: Top Products by Revenue ---
if 'Product name' in df.columns and 'Revenue generated' in df.columns:
    plt.figure(figsize=(10, 6))
    df.groupby('Product name')['Revenue generated'].sum().sort_values(ascending=False).head(10).plot(kind='bar')
    plt.title("Top 10 Products by Revenue")
    plt.xticks(rotation=45)
    plt.tight_layout()
    pdf.savefig()
    plt.close()

# --- Map Visualization (Folium for HTML with Heatmap ) ---
if 'Latitude' in df.columns and 'Longitude' in df.columns and 'Revenue generated' in df.columns:
    # Filter out rows with missing lat/lon for mapping
    df_map = df.dropna(subset=['Latitude', 'Longitude']).copy()

    if not df_map.empty:
        # Calculate initial map center
        mean_lat = df_map['Latitude'].mean()
        mean_lon = df_map['Longitude'].mean()

        supply_chain_map = folium.Map(location=[mean_lat, mean_lon], zoom_start=4)

        # Create Heatmap layer
        heatmap_data = [[row['Latitude'], row['Longitude'], row['Revenue generated']] for index, row in df_map.iterrows() if pd.notna(row['Latitude']) and pd.notna(row['Longitude'])]
        HeatMap(heatmap_data).add_to(supply_chain_map)

        # Save the Folium map as an HTML file
        map_html_path = "supply_chain_heatmap.html"
        supply_chain_map.save(map_html_path)
        print(f"✅ Interactive heatmap saved to '{map_html_path}'")

    else:
        print("Skipping map generation: No valid Latitude/Longitude data after dropping NaNs.")


else:
    print("Skipping map generation: 'Latitude', 'Longitude', or 'Revenue generated' columns not found.")


# Save the PDF
pdf.close()
print("✅ PDF 'supply_chain_analysis_graphs.pdf' created with all visualizations.")

