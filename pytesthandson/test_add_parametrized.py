import pytest
from add_func_with_parametrized import add


@pytest.mark.parametrize("a,b,expected",
                 [
                     (2,3,5),
                     (0,0,0),
                     (-1,1,0),
                     (100,200,300)
                 ]       )
def test_addition(a,b,expected):
    assert add(a,b) == expected