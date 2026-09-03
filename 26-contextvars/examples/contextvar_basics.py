"""ContextVar basics: a variable that can hold a DIFFERENT value per
execution context (roughly: per async task), instead of one shared global
value. `.set()` returns a Token that `.reset()` can use to restore the
previous value exactly.

Run: python3 contextvar_basics.py
"""
from __future__ import annotations
import contextvars

user_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("user_id", default="anonymous")


if __name__ == "__main__":
    print(user_id_var.get())  # anonymous -- the default, nothing set yet

    token = user_id_var.set("user-42")
    print(user_id_var.get())  # user-42

    user_id_var.set("user-99")  # overwrite again
    print(user_id_var.get())  # user-99

    user_id_var.reset(token)  # restore to whatever it was BEFORE the first .set()
    print(user_id_var.get())  # anonymous -- back to the default
