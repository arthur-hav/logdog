import random
import time
import json


KEY_CHOICE = ["host", "method", "process", "cpu", "time"]
VAL_CHOICE = ["some-host", "some-method", "test", "event", "toto", "string"]


def gen_rec(d):
    r = random.random()
    for i in range(3):
        k = random.choice(KEY_CHOICE)
        if r < 0.3:
            d[k] = random.random()
        elif r < 0.6:
            d[k] = [random.randint(0, 10) for i in range(4)]
        elif r < 0.9:
            d[k] = random.choice(VAL_CHOICE)
        else:
            d[k] = {}
            gen_rec(d[k])


lines = []
with open("test.log", "a") as f:
    while True:
        r = random.random()
        if r < 0.9:
            level = "INFO"
        elif r < 0.97:
            level = "WARNING"
        else:
            level = "ERROR"
        d = {"level": level}
        gen_rec(d)

        f.write(json.dumps(d) + "\n")
        f.flush()
        time.sleep(0.001)
