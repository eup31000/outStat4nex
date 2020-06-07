from outStat4nex.out_stat_4nex import main
import os

# Test single field .out with txt export
def test_csv_export_sf():
    test_single_field_out = r"tests/data/spe3-qgnet.out"
    test_single_field_stat_txt = os.path.splitext(test_single_field_out)[0] + "_stat.txt"

    # Remove file in test data folder
    try:
        os.remove(test_single_field_stat_txt)
    except OSError:
        pass

    # Simply call main() with 3 command line like arguments in a list
    main([test_single_field_out, "-f", "txt"])
    assert(os.path.isfile(test_single_field_stat_txt) and os.stat(test_single_field_stat_txt).st_size > 0)

# Test single field .out with Excel export
def test_xls_export_sf():
    test_single_field_out = r"tests/data/spe3-qgnet.out"
    test_single_field_stat_xls = os.path.splitext(test_single_field_out)[0] + "_stat.xlsx"

    # Remove file in test data folder
    try:
        os.remove(test_single_field_stat_xls)
    except OSError:
        pass

    # Simply call main() with 3 command line like arguments in a list
    main([test_single_field_out])
    assert(os.path.isfile(test_single_field_stat_xls) and os.stat(test_single_field_stat_xls).st_size > 0)

# Test multi-field .out with txt export
def test_csv_export_mf():
    test_multi_field_out = r"tests/data/rffm.out"
    test_multi_field_stat_txt = os.path.splitext(test_multi_field_out)[0] + "_stat.txt"

    # Remove file in test data folder
    try:
        os.remove(test_multi_field_stat_txt)
    except OSError:
        pass

    # Simply call main() with 3 command line like arguments in a list
    main([test_multi_field_out, "-f", "txt"])
    assert(os.path.isfile(test_multi_field_stat_txt) and os.stat(test_multi_field_stat_txt).st_size > 0)

# Test multi-field .out with Excel export
def test_xls_export_mf():
    test_multi_field_out = r"tests/data/rffm.out"
    test_multi_field_stat_xls = os.path.splitext(test_multi_field_out)[0] + "_stat.xlsx"

    # Remove file in test data folder
    try:
        os.remove(test_multi_field_stat_xls)
    except OSError:
        pass

    # Simply call main() with 3 command line like arguments in a list
    main([test_multi_field_out])
    assert(os.path.isfile(test_multi_field_stat_xls) and os.stat(test_multi_field_stat_xls).st_size > 0)
