def main():
    standard: Ticket = Ticket(False)
    matinee: Ticket = Ticket(True)
    print(standard)
    print(matinee)

    order1: Popcorn = Popcorn(2.0, True)
    print(order1)


class Ticket:
    matinee: bool

    def __init__(self, matinee: bool) -> None:
        self.matinee = matinee

    def price(self) -> float:
        if self.matinee:
            return 5.0
        return 8.0

    def __str__(self) -> str:
        """returns a string representation for people"""
        if self.matinee:
            return f"Ticket (matinee) is {self.price()}"
        return f"Ticket is {self.price()}"


class Popcorn:
    size: int
    butter: bool

    def __init__(self, size: int, butter: bool) -> None:
        assert size in [1, 2, 3]
        self.size = size
        self.butter = butter

    def price(self) -> float:
        if self.size == 1:
            cost = 3.0
        elif self.size == 2:
            cost = 5.0
        else:
            cost = 7.0

        if self.butter:
            cost += 1.0

        return cost

    def __str__(self) -> str:
        """Returns a string representation for people."""
        if self.butter:
            return f"Popcorn size {self.size} with butter"
        return f"Popcorn size {self.size} without butter"

    def __repr__(self) -> str:
        """Returns a string representation for developers."""
        return f"Popcorn({self.size}, {self.butter})"
