import pytest
from iseven_func import is_even
def test_iseven():
    assert is_even(4) == True

def test_isnot_even():
    assert is_even(7) == False