ice_cream: dict[str, int] = {
    "chocolate": 12,
    "vanilla": 8,
    "strawberry": 4,
}

for flavor in ice_cream:
    print(f"{flavor} has {ice_cream[flavor]} orders")
