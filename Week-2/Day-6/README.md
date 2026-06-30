# Concept Check
## 1.	When should you use a bar chart vs. a histogram?
### Bar chart
- used for categories (majorly)
- bars have spaces
  
### Histogram
- used for numerical data only
- shows distributions
- bars stick together
- values are grouped into ranges called bins

## 2.	What does a boxplot show that a histogram doesn’t?
- Outliers
- middle of the data (median)
- Quartiles (Q1 and Q3)
- IQR (Inter Quartile Range)
that is: summary of data

## 3.	How do you add labels, title, and legend to a Matplotlib chart?
plt.title("Chart Title")
plt.xlabel("x-label")
plt.ylabel("y-label")
plt.legend()
 - Remember: plt.legend() only works if you've provided a label= argument in your plotting function.

## 4.	What’s a heatmap typically used for in EDA?
A heatmap is commonly used to visualize a correlation matrix, making it easy to identify strong positive, negative, or weak relationships between numeric variables.

## 5.	Why is a pie chart usually a bad choice for data with more than 4-5 categories?
With many categories, slices become too small and similar, making comparisons difficult. Bar charts are much easier to read because people compare lengths more accurately than angles or areas.
