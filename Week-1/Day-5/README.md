# Concept Check
## 1.	When would you use a bar chart vs a histogram?
### Bar Chart
- Most famous for Categorical Data (but also used for numerical and time-based data)
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
- For Numerical Data
- Shows distributions
- each bar represents a range of values (called a bin)
- bars are attached to each other (represent continuity)

Typical uses:
- Age distribution
- Exam score distribution
- Income distribution
- Heights
- Population sizes

```python
plt.hist(df["population_2017"], bins=10) # using matplotlib.pyplot
```
  
## 2.	What is the difference between plt.plot() and sns.lineplot()?
While both create line graphs, here are some of the differences:
### plt.plot()
- is from matplotlib.pyplot library
- is low level function. Programmer has more control. 
- used for arrays, lists and individual x and y values
- Example:
```python
plt.plot(df["year"], df["population"])
```

### sns.lineplot()
- is from seaborn library
- is a bit high level
- designed for dataFrames
- Example:
```python
sns.lineplot(data=df,x="year",y="population")
```


## 3.	What does a boxplot actually show — what are the whiskers?
Boxplot, also known as, "Box and Whisker plot" or "five point summary plot" is a plot that mainly shows three things:
1- lower whisker= Q1-1.5 x IQR
2- upper whisker= Q3+1.5 x IQR
3- IQR= Q3-Q1
The box contains the middle 50% of the data, and the line inside the box represents the median.
any value or data point that lies outside the whiskers is known as an "outlier."

```python
sns.boxplot(y=df["population_2017"])
```
boxplot is useful for:
- Detecting outliers
- Comparing distributions
- Seeing spread
- Comparing multiple groups


## 4.	How do you plot multiple charts in one figure using Matplotlib?
By using "subplots."
Each plot has its own axis.

```python
fig,axes = plt.subplots(2,2)
axes[0,0].hist(df["population_2017"])
axes[0,1].boxplot(df["population_2017"])
axes[1,0].bar(...)
axes[1,1].plot(...)
```

## 5.	What is a heatmap useful for and what kind of data does it work best with?
A heatmap is a 2D visualization technique that uses color to represent magnitude or intensity of values within a dataset.
typically warmer colors indicate higher intensities while cooler ones represent lower intensities.
Heatmaps are commonly used to visualize correlation matrices, making it easy to identify strong positive or negative relationships between numeric variables.

```python
corr = df.corr(numeric_only=True)
sns.heatmap(corr)
```
