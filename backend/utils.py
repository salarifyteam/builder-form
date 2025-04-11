import random
import string
import time


def generate_id():
    timestamp = int(time.time() * 1000)
    random_str = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=4)
    )
    return f"{timestamp}{random_str}"
