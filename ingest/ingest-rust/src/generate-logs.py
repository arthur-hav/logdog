import random
import time


lines = []
with open("test.log", "a") as f:
    while True:
        f.write(
            f"""{{"a": {random.random()}, "b": {[random.randint(0, 10) for i in range(4)]}, "c": "{random.choice(["test", "value", "string", "event"])}" }}\n"""
        )
        f.flush()
        time.sleep(0.1)
