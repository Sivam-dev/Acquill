"""
Configuration package - auth and database setup
"""

from .auth import supabase, signup, signin, signout, get_current_user, restore_session

__all__ = ['supabase', 'signup', 'signin', 'signout', 'get_current_user', 'restore_session']
