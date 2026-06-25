# Task:
# Given a raw NumPy array simulating sensor data (provide a small synthetic dataset),
# compute rolling statistics, normalize the data (z-score), and flag outliers (>2 std dev)
# — no Pandas allowed, NumPy only.

import numpy as np

# let's calculate rolling statistics, i.e., mean, std, z-score and outlier detection but with a window

'''normally, in maths:
mean = sum/n
std = sqrt(sum(x_i - mean)**2/n-1) in loop
z-score = (x - mean)/std


but in numpy, we have:
mean_of_data = np.mean(temperature)
std_of_data = np.std(temperature) # uses population std, divides by n

for sample std (which divides by n-1): np.std(temperature, ddof=1)

numpy doesn't have built-in function for z-score
z_scores = (temperature - mean_of_data) / std_of_data
'''

# necessary functions
def calc_rolling_stats(temperature,window):
    rolling_means = []
    rolling_stds = []

    for i in range(len(temperature) - window + 1):

        current_window = temperature[i:i+window]

        mean_of_window = np.mean(current_window)
        std_of_window = np.std(current_window)

        rolling_means.append(mean_of_window)
        rolling_stds.append(std_of_window)

    rolling_means = np.round(rolling_means, 1)
    rolling_stds = np.round(rolling_stds, 1)

    return rolling_means, rolling_stds

def calc_mean_of_data(temperature):
   mean_of_data = np.mean(temperature)
   return mean_of_data

def calc_std_of_data(temperature):
   std_of_data = np.std(temperature)
   return std_of_data

def calc_z_scores(temperature,mean_of_data,std_of_data):
    z_scores = (temperature - mean_of_data) / std_of_data
    return z_scores

def flag_outliers(z_scores):
   outliers = np.abs(z_scores) > 2
   return outliers

def outlier_details(temperature,outliers,z_scores):
    for i in range(len(temperature)):
        if outliers[i]:
            print(
                f"Temperature = {temperature[i]}°C, "
                f"Z-score = {z_scores[i]:.2f}"
            )

# main function
def main():
    # I have been feeling really excited about Remote Sensing lately so I kinda wanna use a related dataset
    # sure I can : )

    # this is my scenario for the synthetic dataset:

    '''A Sentinel-2 satellite is monitoring the surface temperature of a region over multiple observation dates.
    One reading is unusually high, possibly indicating a heat event or a sensor anomaly.'''

    temperature = np.array([
        29.1, 29.4, 29.3, 29.5, 29.7,
        30.2, 29.8, 41.2, 30.1, 29.9
    ])

    print("The synthetic dataset values for Sentinel-2 surface temperature:\n", temperature)

    window = 3  # for rolling stats, let's consider a window of 3

    rolling_means, rolling_stds = calc_rolling_stats(temperature,window) # function call

    print("\nRolling means:")
    print(rolling_means)

    print("\nRolling standard deviations:")
    print(rolling_stds)

    # normalize the entire dataset using z-score
    mean_of_data = calc_mean_of_data(temperature) # function call
    std_of_data = calc_std_of_data(temperature) # function call

    z_scores = calc_z_scores(temperature,mean_of_data,std_of_data) # function call

    print("\nZ-scores:")
    print(np.round(z_scores,2))

    # flag outliers (> 2 standard deviations away from mean)
    outliers = flag_outliers(z_scores) # function call

    print("\nOutlier flags:")
    print(outliers)

    print("\nOutlier value(s):")
    print(temperature[outliers])

    print("\nOutlier details:")
    outlier_details(temperature,outliers,z_scores) # function call

if __name__ == "__main__":
   main()