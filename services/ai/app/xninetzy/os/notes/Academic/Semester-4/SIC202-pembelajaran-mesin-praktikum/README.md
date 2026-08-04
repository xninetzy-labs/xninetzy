---
schema_version: 1
type: hebat_semester4_summary
title: "SIC202 — Pembelajaran Mesin (Praktikum)"
course_id: 1710
semester: 4 (2025Genap)
source: HEBAT
tags: [hebat, semester-4, course]
---

# SIC202 — Pembelajaran Mesin (Praktikum)

| | |
|---|---|
| Kode | SIC202 |
| Semester | 4 (Genap 2025/2026) |
| Moodle ID | `1710` |
| Total aktivitas | 27 |
| File materi | 14 |

Lokasi file lokal: `services/ai/data/hebat/downloads/1710/`

---

## Minggu 5

### 📄 5 - Imbalanced DataFile
- File: `5 - Imbalanced Data.pdf` (768 KB, .pdf)
- CMID: `45766`
- Kata: ~413

**Ringkasan Isi:**

PERTEMUAN 5 
IMBALANCED DATA 
 
OVERSAMPLING (SMOTE) 
import matplotlib.pyplot as plt 
import seaborn as sns 
import pandas as pd 
from imblearn.over_sampling import SMOTE 
 
# Gantilah dengan nama file dataset 
df = pd.read_csv("titanicEdit.csv") 
 
# Bersihkan nama kolom dari spasi tersembunyi 
df.columns = df.columns.str.strip() 
 
# Cek apakah kolom 'Survived' ada 
if 'Survived' not in df.columns: 
    print("Error: Kolom 'Survived' tidak ditemukan dalam dataset.") 
    exit() 
 
# Menampilkan beberapa baris pertama 
print(df.head()) 
 
# Diagram Batang Survived 
survived_counts = df['Survived'].value_counts() 
survived_counts.index = ['Meninggal', 'Selamat'] 
print(survived_counts) 
 
# Plot 
plt.figure(figsize=(6,4)) 
sns.barplot(x=survived_counts.index, y=survived_counts.values, palette='coolwarm') 
 
# Menambahkan label 
plt.xlabel("Status") 
plt.ylabel("Jumlah") 
plt.title("Jumlah Penumpang yang Selamat dan Meninggal") 
plt.show() 
 
missing = df.isna().sum() 
print(missing) 
 
# Pilih fitur (X) dan target (y) 
X = df.drop(columns=['Survived']) 
y = df['Survived'] 
 
# Terapkan SMOTE 
smote = SMOTE(random_state=42) 
X_resampled, y_resampled = smote.fit_resample(X, y) 

 
# Cek distribusi sebelum dan sesudah SMOTE 
# --- Distribusi Sesudah SMOTE --- 
print("Distribusi Sebelum SMOTE:") 
print(y.value_counts()) 
plt.figure(figsize=(6,4)) 
sns.barplot(x=y.value_counts().index, y=y.value_counts().values, 
palette='coolwarm') 
plt.xticks(ticks=[0,1], labels=['Meninggal', 'Selamat']) 
plt.xlabel("Status") 
plt.ylabel("Jumlah") 
plt.title("Distribusi Sebelum SMOTE") 
plt.show() 
 
# --- Distribusi Sesudah SMOTE --- 
print("\nDistribusi Sesudah SMOTE:") 
print(pd.Series(y_resampled).value_counts()) 
plt.figure(figsize=(6,4)) 
sns.barplot(x=pd.Series(y_resampled).value_counts().index,  
            y=pd.Series(y_resampled).value_counts().values,  
            palette='coolwarm') 
plt.xticks(ticks=[0,1], labels=['Meninggal', 'Selamat']) 
plt.xlabel("Status") 
plt.ylabel("Jumlah") 
plt.title("Distribusi Sesudah SMOTE") 
plt.show() 
 
print("\nJumlah data setelah SMOTE:") 
print(X_resampled, y_resampled) 
 
Output : 
 
 


UNDERSAMPLING (RANDOM) 
import matplotlib.pyplot as plt 
import seaborn as sns 
import pandas as pd 
from imblearn.under_sampling import RandomUnderSampler 
 
# Gantilah dengan nama file dataset 
df = pd.read_csv("titanicEdit.csv") 
 
# Bersihkan nama kolom dari spasi tersembunyi 
df.columns = df.columns.str.strip() 
 
# Cek apakah kolom 'Survived' ada 
if 'Survived' not in df.columns: 
    print("Error: Kolom 'Survived' tidak ditemukan dalam dataset.") 
    exit() 
 
# Menampilkan beberapa baris pertama 
print(df.head()) 
 
# Diagram Batang Survived 
survived_counts = df['Survived'].value_counts() 
survived_counts.index = ['Meninggal', 'Selamat'] 
print(survived_counts) 
 
# Plot 
plt.figure(figsize=(6,4)) 
sns.barplot(x=survived_counts.index, y=survived_counts.values, palette='coolwarm') 
 
# Menambahkan label 
plt.xlabel("Status
 _(…dipotong)_

## Minggu 6

### 📄 6- Seleksi dan Ektraksi FiturFile
- File: `6- Seleksi dan Ektraksi Fitur.pdf` (456 KB, .pdf)
- CMID: `50040`
- Kata: ~554

**Ringkasan Isi:**

PERTEMUAN 6 
SELEKSI DAN EKSTRAKSI FITUR 
 
Seleksi Fitur 
Chi Square 
import pandas as pd 
from sklearn.preprocessing import LabelEncoder 
import pandas as pd 
from scipy.stats import chi2_contingency 
 
# Memuat dataset 
df = pd.read_csv("diabetes.csv") 
 
# Membuat LabelEncoder 
#le = LabelEncoder() 
 
# Mengganti kolom "Gender" dengan hasil encoding 
#df['Gender'] = le.fit_transform(df['Gender']) 
 
# Menampilkan hasil 
#print(df) 
 
# Melakukan uji chi-square 
# Mall_Customers 
#contingency_table = pd.crosstab(df['Gender'], df['Spending Score (1-100)']) 
#contingency_table = pd.crosstab(df['Age'], df['Spending Score (1-100)']) 
#contingency_table = pd.crosstab(df['Age'], df['Annual Income (k$)']) 
#contingency_table = pd.crosstab(df['Gender'], df['Annual Income (k$)']) 
#contingency_table = pd.crosstab(df['Gender'], df['Age']) 
 
# Diabetes 
contingency_table = pd.crosstab(df['Glucose'], df['Outcome']) 
#contingency_table = pd.crosstab(df['BMI'], df['Outcome']) 
#contingency_table = pd.crosstab(df['Insulin'], df['Outcome']) 
#contingency_table = pd.crosstab(df['SkinThickness'], df['Outcome']) 
#contingency_table = pd.crosstab(df['BloodPressure'], df['Outcome']) 
#contingency_table = pd.crosstab(df['Age'], df['Outcome']) 
 
#print("Tabel Kontingensi:\n", contingency_table) 
 
 
 
# Melakukan uji chi-square 
chi2, p, dof, expected = chi2_contingency(contingency_table) 
 
# Menampilkan hasil 
print(f"Chi-Square Value: {chi2}") 

print(f"P-Value: {p}") 
 
# Menentukan apakah ada hubungan signifikan 
alpha = 0.05 
if p < alpha: 
    print("Terdapat hubungan signifikan antara Glucose dan Outcome") 
else: 
    print("Tidak terdapat hubungan signifikan antara antara Glucose dan Outcome.") 
 
Output : 
 
 
Ringkasnya: 
 Chi-Square = semua variabel kategorik. 
 Campuran kategorik + numerik → numerik harus dikelompokkan (kalau tetap mau 
Chi-Square). 
 Fitur numerik dengan target numerik. 
o Pearson correlation → untuk hubungan linear 
o Spearman correlation → untuk hubungan monotonic (tidak harus linear) 
 Fitur numerik dengan target kategori (classification) 
o ANOVA (Analysis of Variance) 
 Feature Importance (Tree-Based Model) 
 SHAP Feature Selection 
 
Interpretasi p-value: 
p < 0.05 → hubungan signifikan secara statistik (ada bukti cukup bahwa variabel 
berkorelasi). 
p ≥ 0.05 → hubungan tidak signifikan (tidak ada bukti kuat adanya korelasi) 
 
 
 
 
 
 
 
 


Ekstraksi Fitur 
PCA 
import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt 
from sklearn.decomposition import PCA 
from sklearn.preprocessing import StandardScaler 
 
# Memuat dataset 
df = pd.read_csv("diabetes.csv") 
 
# Memisahkan fitur dan target 
X = df.drop(columns=["Outcome"])  # Hanya fitur numerik 
y = df["Outcome"]  # Target 
 
# Standarisasi data (PCA membutuhkan data dalam skala yang sama) 
scaler = StandardScaler() 
X_scaled = scaler.fit_transform(X) 
 
# Melakukan PCA (jumlah komponen bisa dikurangi) 
pca = PCA(n_components=2)  # Mengambil 2 kompone
 _(…dipotong)_

## Minggu 7

### 📄 7 Decision Tree dan Confusion MatrixFile
- File: `7_Decision Tree dan Confusion Matrix.zip` (1610 KB, .zip)
- CMID: `54108`


## UTS

### 📄 Breast cancer datasetFile
- File: `Breast_cancer_dataset.csv` (122 KB, .csv)
- CMID: `63815`
- Kata: ~573

**Ringkasan Isi:**

"id","diagnosis","radius_mean","texture_mean","perimeter_mean","area_mean","smoothness_mean","compactness_mean","concavity_mean","concave points_mean","symmetry_mean","fractal_dimension_mean","radius_se","texture_se","perimeter_se","area_se","smoothness_se","compactness_se","concavity_se","concave points_se","symmetry_se","fractal_dimension_se","radius_worst","texture_worst","perimeter_worst","area_worst","smoothness_worst","compactness_worst","concavity_worst","concave points_worst","symmetry_worst","fractal_dimension_worst",
842302,M,17.99,10.38,122.8,1001,0.1184,0.2776,0.3001,0.1471,0.2419,0.07871,1.095,0.9053,8.589,153.4,0.006399,0.04904,0.05373,0.01587,0.03003,0.006193,25.38,17.33,184.6,2019,0.1622,0.6656,0.7119,0.2654,0.4601,0.1189
842517,M,20.57,17.77,132.9,1326,0.08474,0.07864,0.0869,0.07017,0.1812,0.05667,0.5435,0.7339,3.398,74.08,0.005225,0.01308,0.0186,0.0134,0.01389,0.003532,24.99,23.41,158.8,1956,0.1238,0.1866,0.2416,0.186,0.275,0.08902
84300903,M,19.69,21.25,130,1203,0.1096,0.1599,0.1974,0.1279,0.2069,0.05999,0.7456,0.7869,4.585,94.03,0.00615,0.04006,0.03832,0.02058,0.0225,0.004571,23.57,25.53,152.5,1709,0.1444,0.4245,0.4504,0.243,0.3613,0.08758
84348301,M,11.42,20.38,77.58,386.1,0.1425,0.2839,0.2414,0.1052,0.2597,0.09744,0.4956,1.156,3.445,27.23,0.00911,0.07458,0.05661,0.01867,0.05963,0.009208,14.91,26.5,98.87,567.7,0.2098,0.8663,0.6869,0.2575,0.6638,0.173
84358402,M,20.29,14.34,135.1,1297,0.1003,0.1328,0.198,0.1043,0.1809,0.05883,0.7572,0.7813,5.438,94.44,0.01149,0.02461,0.05688,0.01885,0.01756,0.005115,22.54,16.67,152.2,1575,0.1374,0.205,0.4,0.1625,0.2364,0.07678
843786,M,12.45,15.7,82.57,477.1,0.1278,0.17,0.1578,0.08089,0.2087,0.07613,0.3345,0.8902,2.217,27.19,0.00751,0.03345,0.03672,0.01137,0.02165,0.005082,15.47,23.75,103.4,741.6,0.1791,0.5249,0.5355,0.1741,0.3985,0.1244
844359,M,18.25,19.98,119.6,1040,0.09463,0.109,0.1127,0.074,0.1794,0.05742,0.4467,0.7732,3.18,53.91,0.004314,0.01382,0.02254,0.01039,0.01369,0.002179,22.88,27.66,153.2,1606,0.1442,0.2576,0.3784,0.1932,0.3063,0.08368
84458202,M,13.71,20.83,90.2,577.9,0.1189,0.1645,0.09366,0.05985,0.2196,0.07451,0.5835,1.377,3.856,50.96,0.008805,0.03029,0.02488,0.01448,0.01486,0.005412,17.06,28.14,110.6,897,0.1654,0.3682,0.2678,0.1556,0.3196,0.1151
844981,M,13,21.82,87.5,519.8,0.1273,0.1932,0.1859,0.09353,0.235,0.07389,0.3063,1.002,2.406,24.32,0.005731,0.03502,0.03553,0.01226,0.02143,0.003749,15.49,30.73,106.2,739.3,0.1703,0.5401,0.539,0.206,0.4378,0.1072
84501001,M,12.46,24.04,83.97,475.9,0.1186,0.2396,0.2273,0.08543,0.203,0.08243,0.2976,1.599,2.039,23.94,0.007149,0.07217,0.07743,0.01432,0.01789,0.01008,15.09,40.68,97.65,711.4,0.1853,1.058,1.105,0.221,0.4366,0.2075
845636,M,16.02,23.24,102.7,797.8,0.08206,0.06669,0.03299,0.03323,0.1528,0.05697,0.3795,1.187,2.466,40.51,0.004029,0.009269,0.01101,0.007591,0.0146,0.003042,19.19,33.88,123.8,1150,0.1181,0.1551,0.1459,0.09975,0.2948,0.08452
84610002,M,15.78,17.89,103.6,781,0.0971,0.1292,0.09954,0.06606,0.1842,0.06082,0.5058,0.9849,3.56
 _(…dipotong)_

### 📄 clinical diabetes datasetFile
- File: `clinical_diabetes_dataset.csv` (531 KB, .csv)
- CMID: `63816`
- Kata: ~1,880

**Ringkasan Isi:**

PatientID,Age,Gender,Ethnicity,SocioeconomicStatus,EducationLevel,BMI,Smoking,AlcoholConsumption,PhysicalActivity,DietQuality,SleepQuality,FamilyHistoryDiabetes,GestationalDiabetes,PolycysticOvarySyndrome,PreviousPreDiabetes,Hypertension,SystolicBP,DiastolicBP,FastingBloodSugar,HbA1c,SerumCreatinine,BUNLevels,CholesterolTotal,CholesterolLDL,CholesterolHDL,CholesterolTriglycerides,AntihypertensiveMedications,Statins,AntidiabeticMedications,FrequentUrination,ExcessiveThirst,UnexplainedWeightLoss,FatigueLevels,BlurredVision,SlowHealingSores,TinglingHandsFeet,QualityOfLifeScore,HeavyMetalsExposure,OccupationalExposureChemicals,WaterQuality,MedicalCheckupsFrequency,MedicationAdherence,HealthLiteracy,Diagnosis,DoctorInCharge
6000,44,0,1,2,1,32.98528363,1,4.499364663,2.443385278,4.898831055,4.049885278,1,1,0,0,0,93,73,163.6871622,9.283631317,2.665606678,28.19014699,254.2706704,86.99362678,70.80146907,190.3358337,0,0,1,0,0,0,9.534168794,0,0,1,73.76510916,0,0,0,1.782724251,4.486979557,7.211348937,1,Confidential
6001,51,1,0,1,2,39.91676413,0,1.578919022,8.30126442,8.941093371,7.508150416,0,0,0,0,0,165,99,188.3470704,7.326870499,4.172176747,32.14949056,155.3588313,110.0561051,39.90011154,81.17246851,0,0,0,0,0,0,0.12321399,0,0,0,91.44575283,0,0,1,3.381069655,5.961704863,5.024612228,1,Confidential
6002,89,1,0,1,3,19.7822513,0,1.177301159,6.103395048,7.722543087,7.708387493,1,0,0,0,0,119,91,127.7036533,4.083425702,1.973168177,10.01837527,231.6089225,62.03579285,62.48066593,279.8090695,1,1,0,0,0,0,9.643320372,0,0,0,54.48574422,0,0,0,2.701018729,8.950820519,7.034943699,0,Confidential
6003,21,1,1,1,2,32.37688079,1,1.714621008,8.645465186,4.80404405,6.286548307,1,1,0,1,0,169,87,82.68841548,6.516644946,3.057796509,44.12328143,176.5923742,68.23840955,46.97781927,112.7513961,0,0,1,0,0,0,3.403556892,0,0,0,77.86675766,0,0,1,1.409055839,3.124768571,4.717774284,0,Confidential
6004,27,1,0,1,3,16.80860027,0,15.46254883,4.629383089,2.532756421,9.771125231,0,0,0,0,0,165,69,90.74339468,5.60722155,4.150353491,7.75711665,157.3441213,66.47621523,40.05975475,381.528785,1,1,0,0,0,0,2.924686838,0,0,0,37.73180801,0,0,0,1.218452269,6.977741342,7.887940038,0,Confidential
6005,65,0,0,0,0,15.82081497,1,17.78102421,9.252521571,2.309158006,9.869400951,0,0,0,0,0,144,64,119.5938388,8.523665495,0.73309125,35.79713471,250.001898,65.2020026,24.70504074,395.4948091,0,1,0,0,0,0,1.973642008,0,0,0,86.37896867,0,0,0,1.535161097,9.682226447,2.744280929,0,Confidential
6006,61,1,2,1,3,20.07514724,0,1.086479327,8.745649626,4.705479904,4.31781287,0,0,0,0,0,109,96,157.0027407,4.52507387,3.624364206,10.78719877,258.393159,104.8524423,24.45778659,83.54635638,0,0,0,1,0,0,6.519586987,0,0,0,86.03693104,0,0,0,0.578207729,1.175503943,1.229452698,0,Confidential
6007,74,1,3,0,3,29.43893837,0,6.18737767,9.114534735,0.180463341,5.365337544,0,1,0,0,0,128,98,81.50788795,7.426381755,0.97922152,36.84418937,159.3386889,108.5487135,39.44800859,121.6742766,0,0,0,0,0,1,2.314413421,0,0,0,47.31581975,0,0,0,1.659423782,2.2583
 _(…dipotong)_

### 📄 diabetes imbalanced datasetFile
- File: `diabetes_imbalanced_dataset.csv` (23 KB, .csv)
- CMID: `63817`
- Kata: ~770

**Ringkasan Isi:**

Pregnancies,Glucose,BloodPressure,SkinThickness,Insulin,BMI,DiabetesPedigreeFunction,Age,Outcome
6,148,72,35,0,33.6,0.627,50,0
1,85,66,29,0,26.6,0.351,31,0
8,183,64,0,0,23.3,0.672,32,0
1,89,66,23,94,28.1,0.167,21,0
0,137,40,35,168,43.1,2.288,33,0
5,116,74,0,0,25.6,0.201,30,0
3,78,50,32,88,31,0.248,26,0
10,115,0,0,0,35.3,0.134,29,0
2,197,70,45,543,30.5,0.158,53,0
8,125,96,0,0,0,0.232,54,0
4,110,92,0,0,37.6,0.191,30,0
10,168,74,0,0,38,0.537,34,0
10,139,80,0,0,27.1,1.441,57,0
1,189,60,23,846,30.1,0.398,59,0
5,166,72,19,175,25.8,0.587,51,0
7,100,0,0,0,30,0.484,32,0
0,118,84,47,230,45.8,0.551,31,0
7,107,74,0,0,29.6,0.254,31,0
1,103,30,38,83,43.3,0.183,33,0
1,115,70,30,96,34.6,0.529,32,0
3,126,88,41,235,39.3,0.704,27,0
8,99,84,0,0,35.4,0.388,50,0
7,196,90,0,0,39.8,0.451,41,0
9,119,80,35,0,29,0.263,29,0
11,143,94,33,146,36.6,0.254,51,0
10,125,70,26,115,31.1,0.205,41,0
7,147,76,0,0,39.4,0.257,43,0
1,97,66,15,140,23.2,0.487,22,0
13,145,82,19,110,22.2,0.245,57,0
5,117,92,0,0,34.1,0.337,38,0
5,109,75,26,0,36,0.546,60,0
3,158,76,36,245,31.6,0.851,28,0
3,88,58,11,54,24.8,0.267,22,0
6,92,92,0,0,19.9,0.188,28,0
10,122,78,31,0,27.6,0.512,45,0
4,103,60,33,192,24,0.966,33,0
11,138,76,0,0,33.2,0.42,35,0
9,102,76,37,0,32.9,0.665,46,0
2,90,68,42,0,38.2,0.503,27,0
4,111,72,47,207,37.1,1.39,56,0
3,180,64,25,70,34,0.271,26,0
7,133,84,0,0,40.2,0.696,37,0
7,106,92,18,0,22.7,0.235,48,0
9,171,110,24,240,45.4,0.721,54,0
7,159,64,0,0,27.4,0.294,40,0
0,180,66,39,0,42,1.893,25,0
1,146,56,0,0,29.7,0.564,29,0
2,71,70,27,0,28,0.586,22,0
7,103,66,32,0,39.1,0.344,31,0
7,105,0,0,0,0,0.305,24,0
1,103,80,11,82,19.4,0.491,22,0
1,101,50,15,36,24.2,0.526,26,0
5,88,66,21,23,24.4,0.342,30,0
8,176,90,34,300,33.7,0.467,58,0
7,150,66,42,342,34.7,0.718,42,0
1,73,50,10,0,23,0.248,21,0
7,187,68,39,304,37.7,0.254,41,0
0,100,88,60,110,46.8,0.962,31,0
0,146,82,0,0,40.5,1.781,44,0
0,105,64,41,142,41.5,0.173,22,0
2,84,0,0,0,0,0.304,21,0
8,133,72,0,0,32.9,0.27,39,0
5,44,62,0,0,25,0.587,36,0
2,141,58,34,128,25.4,0.699,24,0
7,114,66,0,0,32.8,0.258,42,0
5,99,74,27,0,29,0.203,32,0
0,109,88,30,0,32.5,0.855,38,0
2,109,92,0,0,42.7,0.845,54,0
1,95,66,13,38,19.6,0.334,25,0
4,146,85,27,100,28.9,0.189,27,0
2,100,66,20,90,32.9,0.867,28,1
5,139,64,35,140,28.6,0.411,26,0
13,126,90,0,0,43.4,0.583,42,1
4,129,86,20,270,35.1,0.231,23,0
1,79,75,30,0,32,0.396,22,0
1,0,48,20,0,24.7,0.14,22,0
7,62,78,0,0,32.6,0.391,41,0
5,95,72,33,0,37.7,0.37,27,0
0,131,0,0,0,43.2,0.27,26,0
2,112,66,22,0,25,0.307,24,0
3,113,44,13,0,22.4,0.14,22,0
2,74,0,0,0,0,0.102,22,0
7,83,78,26,71,29.3,0.767,36,0
0,101,65,28,0,24.6,0.237,22,0
5,137,108,0,0,48.8,0.227,37,0
2,110,74,29,125,32.4,0.698,27,0
13,106,72,54,0,36.6,0.178,45,0
2,100,68,25,71,38.5,0.324,26,0
15,136,70,32,110,37.1,0.153,43,0
1,107,68,19,0,26.5,0.165,24,0
1,80,55,0,0,19.1,0.258,21,0
4,123,80,15,176,32,0.443,34,0
7,81,78,40,48,46.7,0.261,42,0
4,134,72,0,0,23.8,0.277,60,0
2,142,82,18,64,24.7,0.761,21,0
6,144,72,27,228,33.9,0.255,40,0
2,92,62,28,0,31.6,0.13,24,0
1,71,48,18,76,20.4,0.323
 _(…dipotong)_

## Minggu 10

### 📄 Pertemuan 10 ClusteringFile
- File: `Pertemuan 10 Clustering.pdf` (414 KB, .pdf)
- CMID: `74543`
- Kata: ~818

**Ringkasan Isi:**

MODUL 10 
CLUSTERING 
 
Clustering adalah seperangkat teknik yang digunakan untuk mempartisi data ke dalam 
kelompok, atau cluster berdasarkan kemiripan feature. Clustering sering digunakan sebagai 
teknik analisis data untuk menemukan pola menarik dalam  data, seperti kelompok pelanggan 
berdasarkan perilaku mereka ataupun melakukan analisis sentiment pada suatu hal.  
 
K-Means adalah salah satu metode clustering. Algoritma K-Means bekerja dengan cara iteratif 
untuk menemukan kelompok yang optimal. Langkah-langkah umumnya adalah: 
1. Inisialisasi centroid awal , yaitu memilih  titik-titik awal sebagai centroid untuk setiap 
cluster. Biasanya dipilih secara random. 
2. Assign data ke centroid terdekat. 
3. Perbarui centroid untuk setiap cluster. 
4. Melakukan iterasi sampai tercapai keadaan konvergen. 
 
Algoritma K-Means dapat diimplementasi dengan sklearn.cluster.KMeans. pada library scikit-
learn. 
 
Penggunaan library scikit-learn untuk clustering 
1 # import tools 
import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt 
import seaborn as sns 
from sklearn.cluster import KMeans 
 
2 # import data 
df = pd.read_csv('Mall_Customers.csv') 
df.head() 
 
3 # amati bentuk data 
df.shape 
 
4 # Melihat ringkasan statistik deskriptif dari DataFrame  
......#tambahkan code disini 
 
5 # cek null data 
..... #tambahkan code disini 
 
6 # cek outlier 
..... #tambahkan code disini 
 
 
7 # amati bentuk visual masing-masing fitur 
plt.style.use('fivethirtyeight') 
plt.figure(1 , figsize = (15 , 6)) 
n = 0 

for x in ['Age' , 'Annual Income (k$)' , 'Spending Score (1-
100)']: 
  n += 1 
  plt.subplot(1 , 3 , n) 
  plt.subplots_adjust(hspace =0.5 , wspace = 0.5) 
  sns.histplot( 
    df[x], kde=True, 
    stat="density", kde_kws=dict(cut=3), bins = 20) 
  plt.title('Distplot of {}'.format(x)) 
..... #tambahkan code disini untuk menampilkan figure 
 
8 # Ploting untuk mencari relasi antara Age , Annual Income and 
Spending Score 
plt.figure(1 , figsize = (15 , 20)) 
n = 0 
for x in ['Age' , 'Annual Income (k$)' , 'Spending Score (1-
100)']: 
  for y in ['Age' , 'Annual Income (k$)' , 'Spending Score (1-
100)']: 
    n += 1 
    plt.subplot(3 , 3 , n) 
    plt.subplots_adjust(hspace = 0.5 , wspace = 0.5) 
    sns.regplot(x = x , y = y , data = df) 
    plt.ylabel(y.split()[0]+' '+y.split()[1] if len(y.split()) > 
1 else y ) 
..... #tambahkan code disini untuk menampilkan figure 
 
9 # Melihat sebaran Spending Score dan Annual Income pada Gender 
plt.figure(1 , figsize = (15 , 8)) 
for gender in ['Male' , 'Female']: 
  plt.scatter(x = 'Annual Income (k$)',y = 'Spending Score (1-
100)' , 
  data = df[df['Gender'] == gender] ,s = 200 , alpha = 0.5 , 
  label = gender) 
  plt.xlabel('Annual Income (k$)'), plt.ylabel('Spending Score 
(1-100)') 
  plt.title('Annual Income vs Spending Score') 
  plt.legend() 
..... #tambahkan code disini untuk menampilkan figure 
 
10 # Merancang K-Means untuk spending score vs annual income 
# Menentukan nilai k
 _(…dipotong)_

## Minggu 12

### 📄 Pertemuan 12- Deep LearningFile
- File: `Pertemuan 12- Deep Learning.pdf` (218 KB, .pdf)
- CMID: `79840`
- Kata: ~206

**Ringkasan Isi:**

Pertemuan 12 : Deep Learning 
1. Import Library 
import pandas as pd 
import numpy as np 
import seaborn as sns 
import matplotlib.pyplot as plt 
from sklearn.model_selection import train_test_split 
from sklearn.preprocessing import StandardScaler 
from tensorflow.keras.models import Sequential 
from tensorflow.keras.layers import Dense 
from sklearn.metrics import confusion_matrix, classification_report 
 
2. Load dataset    
Dataset : Bla Bla Bla 
 
3. Pisahkan fitur dan label 
a. Variabel Input : Umur, B, sampai M 
b. Variabel Output : N 
 
4. Lakukan Encoding -- > Umur  :  
1 = ≤ 20  
2 = ≥ 21 and ≤ 30  
3 = ≥ 31 and ≤ 40  
4 = ≥ 41 and ≤ 50  
5 = > 50 
 
5. Lakukan Preproprocessing Data 
a. Cek Missing Value  
b. Outlier 
 
6. Split data 
Data training 80% dan Data testing 20% 
 
7. Bangun model klasifikasi 
 
 
8. Compile dan train 
 


9. Evaluasi 
 
 
10. Confusion matrix 
 
11. Tampilkan confusion matrix 
 
12. Laporan klasifikasi 
 
 
 
Tugas :  
1. Tugas dikerjakan secara individu 
2. Lengkapi program diatas.  
3. Buatlah Laporan yang berisi screen shoot dan penjelasannya 
4. File yang dikumpulkan adalah file program python dan laporan 
5. Penamaan file “Deep Learning_NIM. Zip 
6. Tugas dikumpulkan paling lambat hari Minggu / 31 Mei 2026 pukul 23.59 Wib dan  Senin / 1 
Juni 2026 pukul 23.59 Wib

### 📄 Pertemuan 12 Pengantar Deep LearningFile
- File: `Pertemuan 12_Pengantar Deep Learning.pptx` (3452 KB, .pptx)
- CMID: `79838`
- Kata: ~689

**Ringkasan Isi:**

# Slide 1
# Slide 2
# Slide 3
# Slide 4
# Slide 5
Perhatikan!
# Slide 6
Pembuatan Model
Data
Pelatihan
Algoritma Klasifikasi
IF IPK > 3
OR MATDAS =A
THEN tepat_waktu = ‘yes’
Classifier (Model)
# Slide 7
Proses Testing Model
Classifier (MODEL)
Testing Data
Sejauh mana model tepat meramalkan?
# Slide 8
Proses Klasifikasi
Classifier (MODEL)
Data Baru (Tatang, 3.0, A)
Lulus tepat waktu?
# Slide 9
Perlu diketahui
Proses pembuatan model
Data latihan  Model Klasifikasi
Proses testing model
Data testing  Apakah model sudah benar?
Proses klasifikasi
Data yang tidak diketahui kelasnya  kelas data
# Slide 10
Sebelum Klasifikasi
Data cleaning
Preprocess data untuk mengurangi noise dan missing value
Relevance analysis (feature selection)
Memilih atribut yang penting
Membuang atribut yang tidak terkait atau duplikasi.
Data transformation
Generalize and/or normalize data
# Slide 11
# Slide 12
www.its.ac.id/informatika
INSTITUT TEKNOLOGI SEPULUH NOPEMBER, Surabaya - Indonesia
# Slide 13
Apa itu Deep Learning?
Deep Learning adalah cabang pembelajaran mesin yang menggunakan data, muatan, dan muatan data, untuk mengajari komputer cara melakukan hal-hal yang sebelumnya hanya dapat dilakukan manusia.
Misalnya, bagaimana mesin memecahkan masalah persepsi?
# Slide 14
www.its.ac.id/informatika
INSTITUT TEKNOLOGI SEPULUH NOPEMBER, Surabaya - Indonesia
# Slide 15
Deep Learning didasarkan pada konsep jaringan syaraf tiruan, atau sistem komputasi yang meniru cara otak manusia berfungsi.
PRINSIP.
# Slide 16
TEKNOLOGI
Deep Learning adalah bidang yang berkembang pesat, dan arsitektur baru, varian muncul setiap beberapa minggu.
1. Jaringan Syaraf Konvolusi (CNN)
CNN mengeksploitasi spasial-lokal
korelasi dengan menegakkan lokal
pola konektivitas antara
neuron dari lapisan yang berdekatan.
# Slide 17
Arsitektur dari CNN dibagi menjadi 2 bagian besar:
Feature Extraction Layer
Fully-Connected Layer (MLP).
# Slide 18
TEKNOLOGI
2. Jaringan Syaraf Berulang (RNN)
RNN disebut berulang karena mereka melakukan tugas yang sama untuk setiap elemen urutan, dengan keluaran bergantung pada perhitungan sebelumnya. Atau RNN memiliki "memori" yang menangkap informasi tentang apa yang telah dihitung sejauh ini.
# Slide 19
BEKERJA
Pertimbangkan urutan tulisan tangan berikut:
Kebanyakan orang dengan mudah mengenali angka-angka itu sebagai 504192. Kemudahan itu menipu.
Kesulitan pengenalan pola visual menjadi jelas jika Anda mencoba menulis program komputer untuk mengenali angka seperti di atas.
# Slide 20
BEKERJA
# Slide 21
BEKERJA
Gagasan jaringan saraf adalah untuk mengembangkan sistem yang dapat belajar dari contoh-contoh pelatihan besar ini.
Setiap neuron memberikan bobot pada masukannya — seberapa benar atau salahnya relatif terhadap tugas yang dilakukan. Hasil akhir kemudian ditentukan oleh total pembobotan tersebut
Contoh pelatihan
Pendekatan yang sangat mendasar: Pengklasifikasi Biner
# Slide 22
www.its.ac.id/informatika
INSTITUT TEKNOLOGI SEPULUH NOPEMBER, Surabaya - Indonesia
Mengapa D
 _(…dipotong)_

## Minggu 2

### 📄 Pertemuan 2 Deskripsi DataFile
- File: `Pertemuan 2_Deskripsi Data _.pdf` (363 KB, .pdf)
- CMID: `24947`
- Kata: ~75

**Ringkasan Isi:**

Pertemuan 2 
 
 
 
 
Tugas : 
1. Carilah Data bebas (sesuai dengen spreadsheet) 
2. Jelaskan dan buatlah deskripsi data dari data yang digunakan sesuai dengan coding diatas 
3. Tampilkan ringkasan statistik deskriptif dari sebuah DataFrame Pandas menggunakan 
df.describe() dari data yang digunakan 
4. Tugas dikerjakan secara individu 
5. File yang dikumpulkan adalah file python, data, dan screenshot hasil 
6. Penamaan file “Tugas 1_NIM.Zip” 
7. Tugas dikumpulkan paling lambat hari Minggu / 22 Februari 2026 pukul 23.59 Wib

## Minggu 3

### 📄 Pertemuan 3 - Data PreprocessingFile
- File: `Pertemuan 3 - Data Preprocessing.pdf` (409 KB, .pdf)
- CMID: `35068`
- Kata: ~287

**Ringkasan Isi:**

Pertemuan 3 
1. Cek missing value 
 
 
 
 
 


 
import pandas as pd 
# Contoh: Membaca data dari CSV 
df = pd.read_csv("data.csv") 
# Mengecek jumlah missing value per kolom 
print(df.isnull().sum()) 
Hasil : 
 
2. Handling Missing Value 
Menghapus Missing Values (Drop NaN) 
df_cleaned = df.dropna() 
Mengisi dengan Mean (rata-rata) 
df.fillna(df.mean(), inplace=True) 
Mengisi dengan Median – untuk data dengan outlier 
df.fillna(df.median(), inplace=True) 


Mengisi dengan Mode (nilai terbanyak) – untuk kolom kategori 
for col in df.select_dtypes(include=['object']).columns: 
    df[col].fillna(df[col].mode()[0], inplace=True) 
Mengganti missing value dengan nilai rata2 
 
Menghapus missing value  
 
 
3. Deteksi Outlier 
a. Z-Score 
# Menghitung Z-score 
kolom_numerik = ['Age', 'Annual Income (k$)', 'Spending Score (1-100)'] 
z_scores = np.abs(stats.zscore(df[kolom_numerik])) 
# Menentukan outlier dengan threshold Z-score > 3  
outliers_z = df[(z_scores > 3).any(axis=1)] 
print("Outlier berdasarkan Z-score:\n", outliers_z) 
Hasil : 
 
b. Boxplot (IQR - Interquartile Range) 
???? 


4. Handling Outlier 
Menghapus Outlier 
df_cleaned = df[(z_scores <= 3).all(axis=1)]  # Menghapus semua baris dengan 
Z-score > 3 
print("Dataset setelah menghapus outlier:\n", df_cleaned) 
 
Mengganti dengan Mean atau Median 
for col in kolom_numerik: median = df[col].median()  
df[col] = np.where((z_scores[col] > 3), median, df[col])  # Ganti outlier dengan 
median 
 
Mengganti dengan Batas Maksimum & Minimum IQR 
for col in kolom_numerik:  
df[col] = np.where(df[col] < batas_bawah[col], batas_bawah[col], df[col]) 
df[col] = np.where(df[col] > batas_atas[col], batas_atas[col], df[col]) 
 
Tugas : 
1. Carilah data bebas 
2. Lakukan Create Data dan Data Preprocessing dengan menggunakan Phyton. 
3. Buatlah laporan yang terdiri dari print screen hasil dan penjelasannya 
4. Berilah nama “ laporan Data Preprocessing_NIM.pdf 
 
Ketentuan : 
1. Tugas dikerjakan secara individu 
2. Tugas terdiri dari Laporan, file phyton, dan data aslinya dan dikumpulkan dengan nama 
“Tugas Data PreProcessing_NIM.Zip 
4. Tugas dikumpulkan paling lambat hari Senin / 23 Februari 2026 pukul 23.59 Wib (Kelas I4) 
dan Selasa / 2 Februari 2026 pukul 23.59 Wib (Kelas I1, I2, dan I3)

## Minggu 4

### 📄 Pertemuan 4-Data TransformationFile
- File: `Pertemuan 4-Data Transformation.pdf` (556 KB, .pdf)
- CMID: `40838`
- Kata: ~657

**Ringkasan Isi:**

PERTEMUAN 4 
TRANSFORMASI DATA 
 
Pada beberapa kasus, variabel cenderung memiliki nilai rentang yang sangat besar. Nilai rentang 
yang sangat besar ini akan mempengaruhi hasil pengelolahan data. Untuk mengatasi masalah ini, 
data harus ditransformasi terlebih dahulu. Normalisasi sering digunakan. Nilai rentang yan besar 
akan menjadi rentang yang tidak terlalu besar. Normalisasi terdapat beberapa metode.. Metode 
normalisasi data yang paling sering digunakan yaitu: 
Normalisasi Data pada Phyton 
1. Simple Feature Scaling 
Simple Feature Scaling merupakan metode normalisasi data dengan menskalakan data diantara 0 
dan 1. Metode ini menggunakan rumus: 
𝑋′
𝑖 =  𝑋𝑖
𝑀𝑎𝑥(𝑋) 
Misalnya data X = [7 10 15 20 25] 
o 𝑋′
1 =  
7
25 = 0.28 
o 𝑋′
2 =  
10
25 = 0,4 
o 𝑋′
3 =  
15
25 = 0,6 
o 𝑋′
4 =  
20
25 = 0,8 
o 𝑋′
5 =  
25
25 = 1 
Normalisasi setiap atribut dapat menerapkan kode berikut. Nilai atribut yang akan dinormalisasi 
atribut ‘umur’ dan ‘gaji’. 
  
2. Min-Max Normalization 
Min-max merupakan metode normalisasi data dengan menskalakan data diantara 0 dan 1. 
Metode ini menggunakan rumus: 
𝑋′
𝑖 =  𝑋𝑖 − 𝑀𝑖𝑛(𝑋)
𝑀𝑎𝑥(𝑋) − 𝑀𝑖𝑛(𝑋) 
 
 


Misalnya data X = [7 10 15 20 25] 
o 𝑋′
1 =  
7−7
25−7 = 0 
o 𝑋′
2 =  
10−7
25−7 = 0,1667 
o 𝑋′
3 =  
15−7
25−7 = 0,4444 
o 𝑋′
4 =  
20−7
25−7 = 0,7222 
o 𝑋′
5 =  
25−7
25−7 = 1 
Perbandingan data sebelum dan sesudah di normalisasi ditunjukkan pada Tabel 1. X adalah data 
sebelum dinormalisasi dan X’ adalah data setelah dinormalisasi. Rentang data X berada diantara 
7 dan 25 sedangkan setelah dinormalisasi rentang data menjadi diantara 0 dan 1. 
Tabel 1. Perbandingan data sebelum dan sesudah dinormalisasi 
X X’ 
7 0 
10 0,1667 
15 0,4444 
20 0,7222 
25 1 
 
Penjelasan sama seperti bagian diatas. 
 
3.  Z-Score Standardization 
Metode Z-Score Standardization merupakan metode yang menskalakan selisih antara nilai pada 
data dan rata-ratanya dengan nilai standar deviasinya. Metode ini menggunakan rumus: 
 
𝑋′
𝑖 =  𝑋𝑖 − 𝑀𝑒𝑎𝑛(𝑋)
𝜎  
Dengan  
𝜎 =  √∑ (𝑋𝑖−𝑀𝑒𝑎𝑛(𝑋))2𝑛
𝑖=1
𝑛      Keterangan: n = Banyak data 
𝜎 = standar deviasi 
Misalnya data X = [7 10 15 20 25] 
o Mencari nilai rata-rata 
𝑀𝑒𝑎𝑛(𝑋) =  7 + 10 + 15 + 20 + 25
5  


                   =  77
5  
                   = 15,4 
o Mencari standar Deviasi  
𝜎 =  √(7 − 15,4)2 + (10 − 15,4)2 + (15 − 15,4)2 + (20 − 15,4)2 + (25 − 15,4)2
5  
𝜎 =  √70,56 + 29,16 + 0,16 + 21,16 + 92,16
5  
𝜎 =  √213,2
5  
𝜎 =  6,5299 
o 𝑋′
1 =  
7−15,4
6,5299 =  −1,2864 
o 𝑋′
𝑖 =  
10−15,4
6,5299 =  −0,827 
o 𝑋′
𝑖 =  
15−15,4
6,5299 =  −0,0613 
o 𝑋′
𝑖 =  
20−15,4
6,5299 = 0,7044 
o 𝑋′
𝑖 =  
25−15,4
6,5299 = 1,4720 
Perbandingan data sebelum dan sesudah di normalisasi ditunjukkan pada Tabel 2. X adalah data 
sebelum dinormalisasi dan X’ adalah data setelah dinormalisasi. Rentang data X berada diantara 
7 dan 25 sedangkan setelah dinormalisasi rentang data menjadi diantara 1,4720 dan -1,2864. 
Tabel 2. Perbandingan Data Sebelum dan Sesudah dinormalisasi menggunakan Z-Score 
X X’ 
7 -1,2864 
10 -0,827 
15 
 _(…dipotong)_

## Minggu 9

### 📄 Pertemuan 9 Prakt MLFile
- File: `Pertemuan 9 Prakt ML.pdf` (3987 KB, .pdf)
- CMID: `71590`
- Kata: ~400

**Ringkasan Isi:**

PERTEMUAN 9 
REGRESI 
# Prediksi Harga Saham / Emas dengan Linear Regression 
import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt 
from sklearn.model_selection import train_test_split 
from sklearn.linear_model import LinearRegression 
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score 
# ------------------------------------------------------ 
#    Contoh: Membuat dataset dummy (bisa diganti CSV nyata) 
# ------------------------------------------------------ 
# Misal: kolom 'Date' dan 'Close' (harga penutupan) 
np.random.seed(42) 
days = np.arange(1, 101)  # 100 hari 
price = 100 + 0.5 * days + np.random.normal(0, 3, size=len(days))  # harga naik Perlahan
data = pd.DataFrame({'Day': days, 'Close': price}) 
# Jika punya file CSV asli, bisa ganti dengan: 
# data = pd.read_csv('harga_emas.csv') 
print(data.head()) 
# ------------------------------------------------------ 
#    Persiapan fitur dan target 
# ------------------------------------------------------ 
X = data[['Day']]     # fitur (misal: waktu) 
y = data['Close']     # target (harga penutupan) 
# ------------------------------------------------------ 
#    Split data (80% training, 20% testing) 
# ------------------------------------------------------ 
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42) 
# ------------------------------------------------------ 
#    Buat dan latih model Linear Regression 
# ------------------------------------------------------ 
model = LinearRegression()
model.fit(X_train, y_train) 

 
# ------------------------------------------------------ 
#    Prediksi dan evaluasi 
# ------------------------------------------------------ 
y_pred = model.predict(X_test) 
 
# Evaluasi performa model 
mae = mean_absolute_error(y_test, y_pred) 
mse = mean_squared_error(y_test, y_pred) 
rmse = np.sqrt(mse) 
r2 = r2_score(y_test, y_pred) 
 
print("\n=== Hasil Evaluasi Model ===") 
print(f"Mean Absolute Error (MAE): {mae:.3f}") 
print(f"Mean Squared Error (MSE): {mse:.3f}") 
print(f"Root MSE (RMSE): {rmse:.3f}") 
print(f"R² Score: {r2:.3f}") 
 
# ------------------------------------------------------ 
#    Visualisasi hasil prediksi 
# ------------------------------------------------------ 
plt.figure(figsize=(10, 6)) 
plt.scatter(X_test, y_test, color='blue', label='Data Aktual') 
plt.plot(X_test, y_pred, color='red', linewidth=2, label='Prediksi Linear Regression') 
plt.title("Prediksi Harga (Linear Regression)") 
plt.xlabel("Hari") 
plt.ylabel("Harga") 
plt.legend() 
plt.grid(True) 
plt.show() 
 
# ------------------------------------------------------ 
#    Contoh prediksi hari ke-110 
# ------------------------------------------------------ 
day_baru = np.array([[110]]) 
prediksi_harga = model.predict(day_baru) 
print(f"\nPrediksi harga untuk hari ke-110: {prediksi_harga[0]:.2f}") 
  

Tugas :  
1. Buatlah program untuk prediksi harga menggunakan XGBoost, LightGBM → Kelompok Ganjil 
 _(…dipotong)_

## Minggu 14

### 📄 Soal UAS Prak ML 2026File
- File: `Soal UAS Prak ML 2026.pdf` (472 KB, .pdf)
- CMID: `84721`
- Kata: ~572

**Ringkasan Isi:**

Soal UAS S1 Sistem Informasi 2026 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
Input 
Preprocessing & 
Transformation 
Klasifikasi / Regresi  
(Metode Deep Learning 1) 
Klasifikasi / Regresi  
(Metode Deep Learning 2) 
 
Evaluasi & 
Komparasi 
Output 
Data Splitting 
Membandingkan akurasi, 
presisi, recall, dan F1 
Score dari kedua metode 
(Klasifikasi)  
GUI Mobile / 
Website  
Membandingkan MSE, 
MAE, atau R^2 Score 
dari kedua metode  
(Regresi) 

Soal 
Buatlah rancangan studi kasus yang berbeda, di mana satu dataset yang sama dapat diselesaikan 
menggunakan dua metode Deep Learning untuk dibandingkan performanya, lalu 
diimplementasikan ke dalam antarmuka aplikasi mobile / Website (GUI). 
Penjelasan : 
1. Input 
 Penjelasan: Tahap awal di mana mahasiswa mengumpulkan dan memuat data mentah 
(raw data) yang akan digunakan untuk eksperimen. 
 Konteks Deep Learning:  Agar dapat diproses oleh dua metode Deep Learning  
sekaligus sesuai diagram, input ini harus berupa satu dataset yang sama. 
2. Preprocessing 
 Penjelasan: Proses membersihkan dan merapikan data mentah agar siap diproses oleh 
algoritma Deep Learning. Data mentah seringkali memiliki noise atau format yang 
tidak seragam. 
 Konteks Deep Learning: Langkah ini meliputi penanganan nilai yang hilang (missing 
values) dan deteksi outlier. 
3. Transformation 
 Penjelasan: Tahap mengubah struktur atau skala data. 
 Konteks Deep Learning: 
o Scaling: Melakukan normalisasi (misal: MinMaxScaler atau StandardScaler) 
agar nilai data berada di rentang 0-1 atau -1 sampai 1. 
o Windowing: Mengubah data deret waktu linier menjadi potongan -potongan 
berbasis waktu (sliding window). 
4. Data Splitting 
 Penjelasan: Proses membagi seluruh dataset yang telah ditransformasikan ke dalam 3 
bagian terpisah: Data Training, Data Validation, dan Data Testing (misalnya dengan 
rasio 80% : 10% : 10% atau 70% : 20% : 10%). 
5. Klasifikasi / Regresi (Metode Deep Learning 1 & 2) 
Pada tahap ini, alur dipecah menjadi dua jalur paralel untuk menguji data yang sama 
dengan dua pendekatan arsitektur yang berbeda: 
 Metode Deep Learning 1: Data dimasukkan ke dalam jaringan Deep Learning. 
 Metode Deep Learning 2: Data dimasukkan ke dalam jaringan Deep Learning. 
 
 

6. Evaluasi 
 Penjelasan: Tahap pengujian performa kedua model menggunakan data yang belum 
pernah dilihat sebelumnya (Data Testing) untuk melihat model mana yang lebih cerdas 
dan akurat. 
 Konteks Komparasi (Kotak Kanan): 
o Jika Kasus Klasifikasi: Mahasiswa membandingkan nilai Akurasi (kedekatan 
prediksi), Presisi (ketepatan prediksi positif), Recall (kemampuan mendeteksi 
kelas), dan F1-Score (keseimbangan presisi & recall) dari model CNN vs 
LSTM. 
o Jika Kasus Regresi:  Mahasiswa harus mengubah metrik tersebut menjadi 
metrik kontinu seperti MSE (Mean Squared Error)  atau MAE ( Mean 
Absolute Error) untuk melihat model mana yang memiliki tingkat error paling 
kecil. 
7. Output (Hubungan ke GUI) 
 Penjelasan: Tahap akhir d
 _(…dipotong)_
