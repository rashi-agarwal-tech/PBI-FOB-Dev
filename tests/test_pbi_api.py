from pbi_tools.partitions.partition_utils import pad_str_integer


def test_pad_integer():
    pi_test1 = pad_str_integer("1")
    assert pi_test1 == "01"
    pi_test1 = pad_str_integer("7")
    assert pi_test1 == "07"
    pi_test1 = pad_str_integer("11")
    assert pi_test1 == "11"
    pi_test1 = pad_str_integer("111")
    assert pi_test1 == "111"
