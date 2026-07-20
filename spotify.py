import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

base_path = r"C:\Users\Mayan\Downloads"
file_path = os.path.join(base_path, "Spotify_Manual_Correction.xlsx")

# ==========================================
# 1. טעינת הנתונים
# ==========================================
df = pd.read_excel(file_path).dropna(subset=['Genre'])

genre_counts = df.groupby(['Genre', 'Year']).size().reset_index(name='Count')
pivot_table = genre_counts.pivot(index='Genre', columns='Year', values='Count').fillna(0)

pivot_table['Total'] = pivot_table.sum(axis=1)
pivot_table = pivot_table.sort_values(by='Total', ascending=False).drop(columns=['Total'])

# ==========================================
# 2. הגדרות עיצוב אסתטי (פונטים ורקע)
# ==========================================
plt.rcParams['font.family'] = 'Segoe UI'

fig, ax = plt.subplots(figsize=(12, 10))
bg_color = '#F8F9FA'
fig.patch.set_facecolor(bg_color)
ax.set_facecolor(bg_color)

# ==========================================
# 3. ציור מפת החום בסגנון "אריחים צפים"
# ==========================================
sns.heatmap(
    pivot_table,
    cmap="flare",
    annot=True,
    fmt="g",
    linewidths=8,
    linecolor=bg_color,
    square=True,
    cbar_kws={'shrink': 0.5, 'label': 'Number of Tracks'},
    ax=ax,
    # השינוי כאן: הורדנו את הקיבוע של הצבע.
    # עכשיו Seaborn יחשב קונטרסט אוטומטי (לבן על כהה, שחור על בהיר)
    annot_kws={"size": 11, "weight": "bold"}
)

# ==========================================
# 4. פינישים של טקסט וצירים
# ==========================================
plt.title("Spotify Genre Trends", fontsize=24, fontweight='bold', pad=30, color='#2C3E50', loc='left')

plt.xlabel("", fontsize=14)
plt.ylabel("", fontsize=14)

ax.xaxis.tick_top()
ax.tick_params(left=False, top=False)

plt.xticks(fontsize=13, color='#34495E', fontweight='bold')
plt.yticks(fontsize=13, color='#34495E', rotation=0)

plt.tight_layout()

# שמירה והצגה
output_image = os.path.join(base_path, "Spotify_Floating_Tiles_AutoContrast.png")
plt.savefig(output_image, dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight')
print(f"הגרף המעוצב והקריא נשמר בהצלחה בנתיב: {output_image}")

plt.show(block=True)