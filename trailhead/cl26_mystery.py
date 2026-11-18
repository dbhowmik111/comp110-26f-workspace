rooms: dict[str, set[str]] = {
    "Lounge": {"Dr. Lambda", "Mr.Recursion"},
    "Lab": {"Ms. Recursion", "Mr. Off-By-One"},
    "Server Closet": {"Dr. Lambda", "Prof. Pointer", "Mr. Off-By-One"},
}

def difference(a:set[str])


def lone_visitor(rooms: dict[str, set[str]], crime_room: str) -> str:
    """Return the only person in crime_room who was in no other room."""
    suspects: set[str] = rooms[crime_room]
    for room in rooms:
        if room != crime_room:
            suspect = difference(suspects,rooms[room])
    
