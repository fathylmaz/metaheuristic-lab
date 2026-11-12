from math import isclose
from app.objectives import OBJECTIVES


def test_known_optima():
    for obj in OBJECTIVES.values():
        assert isclose(obj.evaluate(*obj.optimum), 0.0, abs_tol=1e-9), obj.id


def test_rastrigin_multimodal():
    assert OBJECTIVES['rastrigin'].evaluate(0, 0) < OBJECTIVES['rastrigin'].evaluate(1, 1)
