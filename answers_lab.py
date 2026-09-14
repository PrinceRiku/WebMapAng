# Question 1 Selection Sort Angie

def selection_sort(array):
    sorted_array = array[:]
    n = len(sorted_array)
    for i in range(n - 1):
        min_index = i
        for j in range(i + 1, n):
            if sorted_array[j] < sorted_array[min_index]:
                min_index = j
        sorted_array[i], sorted_array[min_index] = \
            sorted_array[min_index], sorted_array[i]
    return sorted_array
