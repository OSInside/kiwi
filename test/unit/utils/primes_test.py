from pytest import mark

from kiwi.utils.primes import primes, factors


class TestPrimes:
    @mark.parametrize('highest,number,tail', [
        [10, 4, [3, 5, 7]],
        [11, 5, [5, 7, 11]],
        [100, 25, [83, 89, 97]],
        [1000, 168, [983, 991, 997]],
        [8192, 1028, [8171, 8179, 8191]],
        [9000, 1117, [8969, 8971, 8999]]])
    def test_primes(self, highest, number, tail):
        _primes = list(primes(highest))
        assert number == len(_primes)
        assert tail == _primes[-3:]

    @mark.parametrize('number,threshold,result', [
        [1, None, []],
        [3, None, [3]],
        [21, None, [3, 7]],
        [100, None, [2, 2, 5, 5]],
        [1000, None, [2, 2, 2, 5, 5, 5]],
        [8191, None, [8191]],
        [8191, 8192, [8191]],
        [8999, None, [8999]],
        [8999, 8192, []],
        [9000, None, [2, 2, 2, 3, 3, 5, 5, 5]]])
    def test_factors(self, number, threshold, result):
        _result = list(factors(number, threshold))
        assert result == _result
