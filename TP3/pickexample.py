import pickle

data = {"name": "Ali", "age": 22}

with open("data.pkl", "wb") as f:
    pickle.dump(data, f)

with open("data.pkl", "rb") as f:
    loaded = pickle.load(f)

print(loaded)
