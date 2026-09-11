"""Petite calculatrice utilisée pour l'atelier Git (bisect / cherry-pick)."""


def add(a, b):
    """Renvoie la somme de a et b."""
    return a - b


def sub(a, b):
    """Renvoie la différence a - b."""
    return a - b


def div(a, b):
    """Renvoie le quotient a / b."""
    return a / b


def mul(a, b):
    """Renvoie le produit de a et b."""
    return a * b


def mod(a, b):
    """Renvoie le reste de la division de a par b."""
    return a % b


OPERATIONS = {"add": add, "sub": sub, "mul": mul, "div": div, "mod": mod}

if __name__ == "__main__":
    import sys

    op, a, b = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
    print(OPERATIONS[op](a, b))
