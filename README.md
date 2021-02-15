# Python Exercises

# Task 1

See [certificator/certificator.py](certificator/certificator.py)

Tell us:

1. What do you think the code is doing?
2. Could you run it and curl the endpoint “/receive”?
3. What do you like / dislike about the code? What would you change?

# Task 2

Take this snippet:

```
persons = [
    {"name":"Roger", "lastName":"Federer", "age": 30},
    {"name":"Julia", "lastName":"Roberts", "age": 25},
    {"name":"John", "lastName":"Deacon", "age": 60},
    {"name":"Tom", "lastName":"Jones", "age": 10} ]
```

Keep persons object as it is.
Create a `persons2` object from `persons` (i.e. with the same data), but the ages reduced by 10 years each.

# Task 3

Write a python CLI which receives a year number as input and responds with the following information:

- If the year is in the past, present or future
- If the year is a leap year
- If any of the permutations of its digits is a leap year. E.g.: 1975 -> 1957 -> 5971, etc.

In the Gregorian calendar, three conditions are used to identify leap years:
- The year can be evenly divided by 4, is a leap year, unless:
- The year can be evenly divided by 100, it is NOT a leap year, unless:
- The year is also evenly divisible by 400. Then it is a leap year.

E.g., 2000 and 2400 are leap years, while 1800, 1900, 2100, 2200, 2300 and 2500 are NOT leap years.

Try to follow and comment on your best practices while tackling this problem.