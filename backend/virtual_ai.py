import random

def virtual_prediction():
    return {
        "trend": random.choice(["HOME", "AWAY", "DRAW"]),
        "confidence": random.randint(60,80)
    }