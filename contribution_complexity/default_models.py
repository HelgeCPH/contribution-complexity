import math
from contribution_complexity.complexity_types import ModificationComplexity


# Models used for complexity ranking of modifications
LINE_MODEL = ((-1, 15), (15, 30), (30, 60), (60, 90), (90, math.inf))
HUNK_MODEL = ((-1, 2), (2, 5), (5, 7), (7, 9), (9, math.inf))
METHOD_MODEL = ((-1, 2), (2, 5), (5, 7), (7, 9), (9, math.inf))
# Models used for complexity ranking of multiple commits, i.e., contributions
FILE_MODEL = ((-1, 15), (15, 30), (30, 60), (60, 90), (90, math.inf))
MODIFICATION_KIND_MODEL = ((-1, 1), (1, 2), (2, 3), (3, 4), (4, math.inf))
MOD_COMPL_WEIGHTS = {
    ModificationComplexity.LOW: 1,
    ModificationComplexity.MODERATE: 4,
    ModificationComplexity.MEDIUM: 21,
    ModificationComplexity.ELEVATED: 256,
    ModificationComplexity.HIGH: 3125,
}
MODIFICATION_MODEL = (
    (-1, 195),
    (195, 390),
    (390, 781),
    (781, 1562),
    (1562, math.inf),
)
