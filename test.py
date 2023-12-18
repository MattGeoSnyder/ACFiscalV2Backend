dictionary = {"one": 1, "two": 2, "three": 3}


def print_dict(kwargs):
    print(**kwargs)


print_dict(dictionary)
