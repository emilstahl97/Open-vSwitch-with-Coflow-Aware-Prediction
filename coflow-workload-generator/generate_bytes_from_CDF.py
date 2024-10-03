import numpy as np
from scipy.interpolate import CubicSpline

class CDFGenerator:
    def __init__(self, cdf_file_path):
        self.cdf_file_path = cdf_file_path
        self.x_values, self.y_values = self.read_cdf()
        self.cubic_spline = CubicSpline(self.y_values, self.x_values)

    def read_cdf(self):
        data = np.loadtxt(self.cdf_file_path)
        x_values = data[:, 0]
        y_values = data[:, 1]
        return x_values, y_values

    def generate_byte_size(self):
        rand_value = np.random.rand()
        byte_size = self.cubic_spline(rand_value)
        return int(byte_size)

if __name__ == "__main__":
    cdf_generator = CDFGenerator("Facebook_HadoopDist_All.txt")

    nr_of_numbers = 2853364

    byte_sizes = []

    for _ in range(nr_of_numbers):
        byte_sizes.append(cdf_generator.generate_byte_size())

    print(f"Min: {np.min(byte_sizes)}")
    print(f"Max: {np.max(byte_sizes)}")
    print(f"Mean: {np.mean(byte_sizes)}")
