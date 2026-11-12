"""Canonical two-dimensional minimization test functions."""
from dataclasses import dataclass
from math import cos, exp, pi, sqrt
from typing import Callable


@dataclass(frozen=True)
class Objective:
    id: str
    name: str
    description: str
    bounds: tuple[float, float]
    optimum: tuple[float, float]
    function: Callable[[float, float], float]

    def evaluate(self, x: float, y: float) -> float:
        return float(self.function(x, y))


def sphere(x: float, y: float) -> float:
    return x * x + y * y


def rastrigin(x: float, y: float) -> float:
    return 20 + x * x + y * y - 10 * (cos(2 * pi * x) + cos(2 * pi * y))


def ackley(x: float, y: float) -> float:
    return -20 * exp(-0.2 * sqrt((x * x + y * y) / 2)) - exp(
        (cos(2 * pi * x) + cos(2 * pi * y)) / 2
    ) + 20 + exp(1)


def rosenbrock(x: float, y: float) -> float:
    return (1 - x) ** 2 + 100 * (y - x * x) ** 2


def griewank(x: float, y: float) -> float:
    """Multimodal; global minimizer is (0, 0)."""
    return 1 + (x*x + y*y)/4000 - cos(x)*cos(y/sqrt(2))


def himmelblau(x: float, y: float) -> float:
    """Four global minima in the usual [-5, 5]^2 domain."""
    return (x*x + y - 11)**2 + (x + y*y - 7)**2


def beale(x: float, y: float) -> float:
    """Narrow curved basin with optimum (3, 0.5)."""
    return (1.5-x+x*y)**2 + (2.25-x+x*y*y)**2 + (2.625-x+x*y**3)**2


def booth(x: float, y: float) -> float:
    """Quadratic bowl rotated relative to axes; optimum (1, 3)."""
    return (x+2*y-7)**2 + (2*x+y-5)**2


OBJECTIVES = {
    'sphere': Objective('sphere', 'Sphere', 'Tek minimumlu, konveks referans fonksiyon.', (-5.12, 5.12), (0, 0), sphere),
    'rastrigin': Objective('rastrigin', 'Rastrigin', 'Çok sayıda yerel minimum içeren dalgalı yüzey.', (-5.12, 5.12), (0, 0), rastrigin),
    'ackley': Objective('ackley', 'Ackley', 'Düz dış bölgeleri ve merkezde derin çukuru olan yüzey.', (-5, 5), (0, 0), ackley),
    'rosenbrock': Objective('rosenbrock', 'Rosenbrock', 'Kavisli, dar optimum vadisiyle zorlayıcı yüzey.', (-3, 3), (1, 1), rosenbrock),
    'griewank': Objective('griewank', 'Griewank', 'Dalgacıklı ve çok modlu minimumlar içeren yüzey.', (-6, 6), (0, 0), griewank),
    'himmelblau': Objective('himmelblau', 'Himmelblau', 'Dört farklı global minimumu bulunan yüzey.', (-5, 5), (3, 2), himmelblau),
    'beale': Objective('beale', 'Beale', 'Dar, eğimli ve karmaşık optimum havzası.', (-4.5, 4.5), (3, 0.5), beale),
    'booth': Objective('booth', 'Booth', 'Eğik eksenli kuadratik optimizasyon havzası.', (-10, 10), (1, 3), booth),
}
