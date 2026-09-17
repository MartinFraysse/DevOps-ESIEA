# Test reproductible pour git bisect (volontairement hors du dépôt,
# pour qu'il existe à chaque commit testé).
# Code de sortie : 0 = good, 1 = bad.
import sys

sys.path.insert(0, "src")
from calc import add

sys.exit(0 if add(2, 3) == 5 else 1)
