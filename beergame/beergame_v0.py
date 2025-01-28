# Directory: beergame/
# File: beergame/beergame_v0.py

from beergame.env.beergame import raw_env
from pettingzoo.utils import wrappers

# def env(render_mode=None, **kwargs):
#     """
#     The env function wraps the environment in 3 wrappers by default.
#     """
#     internal_render_mode = render_mode if render_mode != "ansi" else "human"
#     env = raw_env(render_mode=internal_render_mode, **kwargs)
#     # This wrapper is only for environments which print results to the terminal
#     if render_mode == "ansi":
#         env = wrappers.CaptureStdoutWrapper(env)
#     # Provides a wide variety of helpful user errors
#     env = wrappers.AssertOutOfBoundsWrapper(env)
#     env = wrappers.OrderEnforcingWrapper(env)
#     return env