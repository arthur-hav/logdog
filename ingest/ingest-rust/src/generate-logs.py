import random

lines = []
with open("test.log", "a") as f:
    for i in range(50):
        lines.append(
            f"""{{"a": {random.random()}, "b": {[random.randint(0, 10) for i in range(4)]}, "c": "{random.choice(["test", "value", "string", "event"])}" }}"""
        )
    f.write("\n".join(lines))
