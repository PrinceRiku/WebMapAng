import numpy as np
import matplotlib.pyplot as plt

def plot_three_functions(funcs, intervals, npts=2000, labels=None, figsize=(10, 9),
                         suptitle="Function plots", savepath=None, show=True):
    """
    Plot up to three functions, each on its own interval.

    Parameters
    - funcs: list/tuple of callables [f1, f2, f3] (can provide fewer than 3)
    - intervals: list/tuple of (xl, xr) pairs, one per function
    - npts: number of sample points per function (default 2000)
    - labels: optional list of labels for the plots
    - figsize: matplotlib figure size
    - suptitle: overall title
    - savepath: if provided, save the figure to this path
    - show: whether to call plt.show()
    """
    n = min(3, len(funcs))
    if labels is None:
        labels = [f"f{i+1}" for i in range(n)]
    fig, axes = plt.subplots(n, 1, figsize=figsize, squeeze=False)
    for i in range(n):
        ax = axes[i, 0]
        xl, xr = intervals[i]
        x = np.linspace(xl, xr, npts)
        y = funcs[i](x)
        ax.plot(x, y, lw=1.2)
        ax.set_xlim(xl, xr)
        ax.set_xlabel("x")
        ax.set_ylabel(labels[i])
        ax.set_title(labels[i] + f" on [{xl}, {xr}]")
        ax.grid(True)
    fig.suptitle(suptitle)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    if savepath:
        fig.savefig(savepath, dpi=200)
    if show:
        plt.show()
    plt.close(fig)


# Define the three functions described:
def f1(x):
    # f1(x) = |cos(pi x)| on [0,1]
    return np.abs(np.cos(np.pi * x))

def f2(x):
    # f2(x) = cos(x) + 5cos(1.6x) - 2cos(2.0x) + 5cos(4.5x) + 7cos(9.0x) on [2,7]
    return (np.cos(x)
            + 5.0 * np.cos(1.6 * x)
            - 2.0 * np.cos(2.0 * x)
            + 5.0 * np.cos(4.5 * x)
            + 7.0 * np.cos(9.0 * x))

def f3(x):
    # f3(x) = -sech^2(10.0(x-0.2)) + sech^2(100.0(x-0.4)) + sech(1000.0(x-0.6))^2 on [0,1]
    # sech(x) = 1 / cosh(x)
    sech = lambda t: 1.0 / np.cosh(t)
    return (-sech(10.0 * (x - 0.2))**2
            + sech(100.0 * (x - 0.4))**2
            + sech(1000.0 * (x - 0.6))**2)


if __name__ == "__main__":
    # Example usage: plot the three functions on their specified domains.
    functions = [f1, f2, f3]
    intervals = [(0.0, 1.0), (2.0, 7.0), (0.0, 1.0)]
    labels = [
        r"$f_1(x)=|\cos(\pi x)|$",
        r"$f_2(x)=\cos(x)+5\cos(1.6x)-2\cos(2.0x)+5\cos(4.5x)+7\cos(9.0x)$",
        r"$f_3(x)=-\operatorname{sech}^2(10(x-0.2))+\operatorname{sech}^2(100(x-0.4))+\operatorname{sech}^2(1000(x-0.6))$",
    ]
    plot_three_functions(functions, intervals, npts=2000, labels=labels,
                         suptitle="Three example functions", savepath=None, show=True)


def find_min_mc(n, xl, xr, f):
    # Your code here
    return (xmin, ymin), minval

def find_min_mc_wzoom(n, xl, xr, f, nzoom):
    # Your code here
    return (xmin, ymin), minval
