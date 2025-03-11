import matplotlib.pyplot as plt
import numpy as np


def calculate_channel_capacity(alphabet_size):
    p_input = np.ones(alphabet_size) / alphabet_size

    p_output_given_input = np.zeros((alphabet_size, alphabet_size))

    for i in range(alphabet_size):
        if alphabet_size == 1:
            p_output_given_input[0][0] = 1.0
            continue

        p_output_given_input[i][i] = 0.6

        if i == 0:
            p_output_given_input[alphabet_size - 1][i] = 0.2
            p_output_given_input[1][i] = 0.2
        elif i == alphabet_size - 1:
            p_output_given_input[i - 1][i] = 0.2
            p_output_given_input[0][i] = 0.2
        else:
            p_output_given_input[i - 1][i] = 0.2
            p_output_given_input[i + 1][i] = 0.2

    p_output = np.zeros(alphabet_size)
    for j in range(alphabet_size):
        for i in range(alphabet_size):
            p_output[j] += p_input[i] * p_output_given_input[j][i]

    H_Y = 0
    for j in range(alphabet_size):
        if p_output[j] > 0:
            H_Y -= p_output[j] * np.log2(p_output[j])

    H_Y_given_X = 0
    for i in range(alphabet_size):
        for j in range(alphabet_size):
            if p_output_given_input[j][i] > 0:
                H_Y_given_X -= p_input[i] * p_output_given_input[j][i] * np.log2(p_output_given_input[j][i])

    mutual_information = H_Y - H_Y_given_X
    avg_transmission_time = (alphabet_size + 1) / 2

    return mutual_information / avg_transmission_time


def find_optimal_alphabet_size(max_size=100):
    max_capacity = 0
    optimal_size = 0

    for size in range(1, max_size + 1):
        capacity = calculate_channel_capacity(size)
        if capacity > max_capacity:
            max_capacity = capacity
            optimal_size = size

    return optimal_size, max_capacity


def plot_capacity_vs_alphabet_size(optimal_size, max_capacity):
    size_values = range(1, 50)
    capacities = [calculate_channel_capacity(size) for size in size_values]

    plt.figure(figsize=(10, 6))
    plt.plot(size_values, capacities, "b-")
    plt.scatter(
        optimal_size,
        max_capacity,
        color="red",
        s=100,
        label=f"Maximum at N={optimal_size}, ν={max_capacity:.4f} bits/s",
    )
    plt.xlabel("Alphabet Size (N)")
    plt.ylabel("Channel Capacity (bits/s)")
    plt.title("Channel Capacity vs. Alphabet Size (Case 2)")
    plt.grid(True)
    plt.legend()
    plt.savefig("case2_capacity.png")
    plt.show()


def main():
    optimal_size, max_capacity = find_optimal_alphabet_size()

    print(f"Optimal alphabet size: {optimal_size}")
    print(f"Maximum channel capacity: {max_capacity:.4f} bits/s")

    plot_capacity_vs_alphabet_size(optimal_size, max_capacity)


if __name__ == "__main__":
    main()
