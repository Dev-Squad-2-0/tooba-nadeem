# Concept Check
## What is the difference between .drop() and .dropna()?
- .drop() is used to remove any selected column from the dataset (e.g., df.drop(columns=["Age"])
- .dropna() is used to remove null rows/cols from the dataset (e.g., df.dropna())

## How do you change the dtype of a column — and when would you need to?
dtype is basically the data type of a column(or Series). It may be str, int, float, bool ,etc. We need to change dtype whenever we encounter any of these:
- numbers are stored as strings
- dates are stored as strings
- you want calculations
- you want sorting to behave correctly
- you want less memory usage

for example: 
The population cols in my dataset were of type 'str', but I wanted to perform  numerical calculations and so I changed the dtype from 'str' to 'int':
```python
for col in population_cols:
 df[col] = df[col].str.replace(",", "").astype(int)
 ```

## What does .apply() do and how is it different from vectorized operations?
### Vectorized operations
```python
df["population_2017"] * 2
```
- built into Pandas
- very fast
- used for arithmetic and comparisons

### .apply()
```python
def size(population):
    if population > 5000:
        return "Large"
    else:
        return "Small"
        
df["population_2017"].apply(size)
```
- uses your own function
- more flexible
- usually slower
  
## Difference between .pivot() and .pivot_table()?
Both rearrange data into a new table.

Suppose we have: 

| City |	Year |	Sales |
|------|------|-------|
| Lahore | 	2023	| 100 |
| Lahore	| 2024	| 120 |
| Karachi |	2023	| 90 |
| Karachi	| 2024	| 110 |

and we may want:

| City	| 2023 |	2024 |
|------|------|------|
| Lahore	| 100	| 120 |
| Karachi	| 90	| 110 |

That is reshaping.

### .pivot()
- rearranges data
- Works only when every combination is unique.
- Example: Suppose the data is:

| City | Year | Sales |
|------|------|------:|
| Lahore | 2023 | 100 |
| Lahore | 2023 | 120 |

Using the following python code, we combine the duplicate rows by taking their average:
```python
sales.pivot_table(
    index="City",
    columns="Year",
    values="Sales",
    aggfunc="mean"
)
```

| City | 2023 |
|------|------:|
| Lahore | 110 |

#### .pivot_table()
- rearranges and summarizes data
- Can handle duplicate values.
- It combines them using an aggregation function (mean, sum, count, max, min).
- Example:
Suppose the data is:

| City | Year | Sales |
|------|------|------|
| Lahore | 2023 | 100 |
| Lahore | 2023 | 120 |

Using the following python code, we combine the duplicate rows by taking their average:
```python
sales.pivot_table(index="City", columns="Year", values="Sales", aggfunc="mean")
```


| City | 2023 |
|------|------|
| Lahore | 110 |


## What does .merge() do and what are the 4 types of joins?
### .merge()
If we have two DataFrames.
First one:
| ID	| Name |
|----|-------|
| 1	| Ali |
| 2	| Sara |
| 3	| Ahmed |

Second one:
| ID	| Marks |
|----|-------|
| 1	| 80 |
| 2	| 95 |
| 4	| 88 |

Both have the column "ID", so we can combine them.
```python 
pd.merge(df1, df2, on="ID")
```

### 4 types of joins
### - Inner Join
Keeps only matching IDs. (Only the common rows survive.)
```python
pd.merge(df1, df2, on="ID", how="inner")
```
Result
| ID	| Name	| Marks |
|----|------|-------|
| 1	| Ali |	80 |
| 2	| Sara |	95 |

ID 3 and 4 disappear.

### - Left Join
Keeps everything from the left DataFrame. (Keep all rows from the left table.)
```python
pd.merge(df1, df2, on="ID", how="left")
```
Result
| ID	| Name	| Marks |
|----|------|-------|
| 1	| Ali	| 80 |
| 2	| Sara |	95 |
| 3	| Ahmed	| NaN |

Ahmed had no marks. So, Pandas fills in NaN.

### - Right Join
Keeps everything from the right DataFrame.
```python
pd.merge(df1, df2, on="ID", how="right")
```
Result
| ID	| Name	| Marks |
|----|------|-------|
| 1	| Ali	| 80 |
| 2	| Sara	| 95 |
| 4	| NaN	| 88 |

ID 4 exists only in the right table.

### - Outer Join
Keeps everything from both. Nothing is lost.
```python
pd.merge(df1, df2, on="ID", how="outer")
```
Result
| ID |	Name	| Marks |
|----|------|-------|
| 1	| Ali	| 80 |
| 2	| Sara	| 95 |
| 3	| Ahmed	| NaN |
| 4	| NaN	| 88 |
