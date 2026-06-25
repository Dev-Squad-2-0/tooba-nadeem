# Task: Week1_Day1
#  Build a small command-line program: takes a list of numbers as input, 
#  returns mean, median, mode, min, max — without using any external library (pure Python only).
#  Push to GitHub.


# necessary functions
def calc_mean(numbers):
    return sum(numbers) / len(numbers)


def calc_median(numbers): 
    # median is the middlemost value from sorted numbers
    # two cases can be considered: even or odd
    sorted_nums = sorted(numbers)
    n = len(sorted_nums)

    if n % 2 == 1: # odd no.of elements check
        return sorted_nums[n // 2] # middle index is n//2
    else: # for even no.of elements
        mid1 = sorted_nums[n // 2 - 1]
        mid2 = sorted_nums[n // 2]
        return (mid1 + mid2) / 2  # middle is avg of the two central elements


def calc_mode(numbers): # most frequent occuring value
    frequency = {} # empty dictionary for frequencies

    for num in numbers:
        frequency[num] = frequency.get(num, 0) + 1

    max_count = max(frequency.values())

    modes = []
    for num, count in frequency.items(): # check each num and its frequency
        if count == max_count:  # check if this num has the highest frequency
            modes.append(num)

    if len(modes) == len(frequency):   # if every num has the same frequency, there's no mode
        return "No mode"
    elif len(modes) == 1:  # if only one num has the highest frequency, retunr that single num as mode
        return modes[0]
    else:
        return modes # else return all modes

# main function
def main():
    print("Command-Line Program to calculate Stats!")
    user_input = input("Enter numbers separated by spaces: ")

    numbers = [int(x) for x in user_input.split()]

    print("\nResults")
    print("-------")
    print("Mean  :", calc_mean(numbers))
    print("Median:", calc_median(numbers))
    print("Mode  :", calc_mode(numbers))
    print("Min   :", min(numbers))
    print("Max   :", max(numbers))


if __name__ == "__main__":
    main()