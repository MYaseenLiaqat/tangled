# Gradient descent

Gradient descent is an optimisation algorithm that minimises a loss function by repeatedly moving the parameters in the direction of the negative gradient.

The learning rate controls the step size. If the learning rate is too large the loss can diverge or oscillate; if it is too small, training converges very slowly.

Stochastic gradient descent (SGD) estimates the gradient from one example or a mini-batch, which makes each step cheaper but noisier. Momentum averages past gradients to smooth the updates.
