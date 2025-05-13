#exercise 1
import pytest

def sum(a,b):
    return a+b

def test_method():
    assert sum(5,4) == 9
