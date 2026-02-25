Simple plots
============

We start by making a static plot. The syntax is similar to matplotlib: ::

    import squap
    import numpy as np

    x = np.linspace(0, 2*np.pi, 50)
    squap.plot(x, np.sin(x))
    squap.scatter(x, np.cos(x), color="red")

    squap.set_xlim(0, 2*np.pi)
    squap.set_ylim(-1, 1)

    squap.show()

We use :func:`np.linspace <numpy.linspace>` to initialise `x` as `50` evenly spaced points between `0` and :math:`2\pi`.
After this we make a line plot with
