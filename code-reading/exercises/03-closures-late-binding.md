# Exercise 3 — Closures and Late Binding

## 1. Snippet

```python
funcs = []
for i in range(3):
    funcs.append(lambda: i)

print([f() for f in funcs])

funcs2 = []
for i in range(3):
    funcs2.append(lambda i=i: i)

print([f() for f in funcs2])
```

## 2. Your Prediction

What do the two printed lists look like? Are they the same?

## 3. Answer

```text
[2, 2, 2]
[0, 1, 2]
```

## 4. Why

- A closure captures the *variable* `i`, not its value at the time the lambda was created.
  By the time any of the three lambdas in `funcs` actually run, the loop has finished and `i`
  holds its final value, `2` -- so every lambda reads the same, final `i`.
- `lambda i=i: i` in the second loop fixes this by giving the lambda its OWN parameter named
  `i`, whose *default value* is evaluated immediately, at the time each lambda is defined,
  capturing that iteration's value rather than a shared reference to the loop variable.

## 5. 💡 Mental Model

```text
closures capture VARIABLES, not snapshots of their value at definition time
force a snapshot with a default argument: lambda i=i: ...
```
