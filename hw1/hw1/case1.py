import matplotlib.pyplot as plt
import numpy as np


def calculate_channel_capacity(alphabet_size):
    entropy = np.log2(alphabet_size)
    avg_transmission_time = (alphabet_size + 1) / 2
    return entropy / avg_transmission_time


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
    plt.title("Channel Capacity vs. Alphabet Size (Case 1)")
    plt.grid(True)
    plt.legend()
    plt.savefig("case1_capacity.png")
    plt.show()


def main():
    optimal_size, max_capacity = find_optimal_alphabet_size()

    print(f"Optimal alphabet size: {optimal_size}")
    print(f"Maximum channel capacity: {max_capacity:.4f} bits/s")

    plot_capacity_vs_alphabet_size(optimal_size, max_capacity)


if __name__ == "__main__":
    main()
