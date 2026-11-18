def count_ways() -> dict[int, int]:
    """Return a dict whosekeys are the sums 2-12
    and whose values are thenumber of ways
    to roll each sum with two 6-sided dice."""
    ways: dict[int, int] = {}

    for i in range(1, 7):
        for n in range(1, 7):
            for k in range(1, 7):
                sum: int = n + i + k
                if sum in ways:
                    ways[sum] += 1
                else:
                    ways[sum] = 1

    return ways


ways: dict[int, int] = count_ways()
print(ways[7])
print(ways[3])
print(len(ways))
