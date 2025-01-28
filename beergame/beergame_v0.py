"""Beer Game v0 environment registration"""

from beergame.env.beergame import env

def beergame_v0(**kwargs):
    """
    Creates a Beer Game environment with the v0 parameters.
    """
    return env(**kwargs)