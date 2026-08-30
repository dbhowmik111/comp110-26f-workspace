"""My first exercise in COMP110!"""

__author__ = "730986400"


print("Hello World")


def greet(name: str) -> str:  # function greet with arguments name as string
    """A welcoming first function definition."""
    return "Hello, " + name + "!"  # #returns as string -> str


# greet(name="Dikshita")  # call


def greet1(name1: int) -> int:  # 1st REFLECTION QUESTION
    """A welcoming first function definition."""
    return name1 + 1

    # greet1(name1=1)  # call


# greet(greet(name="Dikshita"))  # 2ND REFLECTION QUESTION

if __name__ == "__main__":
    print(greet(name=input("What is your name? ")))
