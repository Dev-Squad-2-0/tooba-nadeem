# Concept Check
## 1.	When would you use a bar chart vs a histogram?
### Bar Chart
- For categorical data
- Shows categories
- each bar represents one category
- bars are separarted by space

Typical uses:
- Average salary by department
- Sales by month
- Population by province
- Students in each class

```python
plt.bar(df["province"], df["population"]) # using matplotlib.pyplot
# OR
sns.barplot(data=df, x="province", y="population") # using seaborn
```
   
### Histogram
- For numerical Data
- Shows distributions
- each bar represents a mix of categories depending upon the specific bin
- bars are attached to each other (represent continuity)

Typical uses:
Age distribution
Exam score distribution
Income distribution
Heights
Population sizes

```python
plt.hist(df["population_2017"], bins=10) # using matplotlib.pyplot
```
  
## 2.	What is the difference between plt.plot() and sns.lineplot()?


## 3.	What does a boxplot actually show — what are the whiskers?

## 4.	How do you plot multiple charts in one figure using Matplotlib?

## 5.	What is a heatmap useful for and what kind of data does it work best with?
