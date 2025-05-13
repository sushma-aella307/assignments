import pytest
from add_function import addition

def test_add():
    assert addition(3,4) == 7
    assert addition(0,2) == 2
    assert addition(0,-2) == -7
    
