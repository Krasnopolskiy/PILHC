import matplotlib.pyplot as plt
import numpy as np


def calculate_channel_capacity(alphabet_size):
    p_unnorm = np.array([1 / (2**i) for i in range(1, alphabet_size + 1)])

    normalization_factor = np.sum(p_unnorm)
    p = p_unnorm / normalization_factor

    entropy = -np.sum(p * np.log2(p, where=p > 0))

    indices = np.arange(1, alphabet_size + 1)
    avg_transmission_time = np.sum(p * indices)

    capacity = entropy / avg_transmission_time

    return capacity


def find_optimal_alphabet_size(max_size=100):
    max_capacity = 0
    optimal_size = 0

    for size in range(1, max_size + 1):
        capacity = calculate_channel_capacity(size)
        print(capacity)
        if capacity > max_capacity:
            max_capacity = capacity
            optimal_size = size

    return optimal_size, max_capacity


def plot_capacity_vs_alphabet_size(optimal_size, max_capacity):
    size_values = range(1, 100)
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
    plt.title("Channel Capacity vs. Alphabet Size (Case 3)")
    plt.grid(True)
    plt.legend()
    plt.savefig("case3_capacity.png")
    plt.show()


def main():
    optimal_size, max_capacity = find_optimal_alphabet_size()

    print(f"Optimal alphabet size: {optimal_size}")
    print(f"Maximum channel capacity: {max_capacity:.4f} bits/s")

    plot_capacity_vs_alphabet_size(optimal_size, max_capacity)


if __name__ == "__main__":
    main()
