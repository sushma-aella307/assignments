import pytest
from division_func import divide

def test_divide_valid():
    assert divide(4,2) == 2

def test_divide_invalid():
    with pytest.raises(ValueError,match="cannot divide by zero"):
        divide(10,0)
