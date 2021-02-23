# Python Exercises

# Task 1

See [task01/task01.py](task01/task01.py)

# Task 2

Tell us:

- What would you need to run the server from task01?
- Try to run the server and `curl` the root endpoint `/`

The query should look something like this:

```
curl -X GET "http://localhost:5000?param1=value1&param2=value2" -H "Authorization: Bearer $token"
```

You can get the token from the `.env` file like this:

```
source .env
echo $token
```

# Task 3

See [task03/task03.py](task03/task03.py)

# Task 4

See [task04/task04.py](task04/task04.py)