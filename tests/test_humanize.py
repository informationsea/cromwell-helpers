from cromwellhelper.humanize import *


def test_humanize_bytes():
    assert humanize_bytes(10) == "10 B"
    assert humanize_bytes(1000) == "1000 B"
    assert humanize_bytes(1023) == "1023 B"
    assert humanize_bytes(1024) == "1.0 kB"
    assert humanize_bytes(int(1024 * 1.1)) == "1.1 kB"
    assert humanize_bytes(int(1024 * 20.3)) == "20.3 kB"
    assert humanize_bytes(int(1024 * 1024) - 1) == "1024.0 kB"
    assert humanize_bytes(int(1024 * 1024)) == "1.0 MB"
    assert humanize_bytes(int(1024 * 1024 * 1024) - 1) == "1024.0 MB"
    assert humanize_bytes(int(1024 * 1024 * 1024)) == "1.0 GB"
    assert humanize_bytes(int(1024 * 1024 * 1024 * 1024) - 1) == "1024.0 GB"
    assert humanize_bytes(int(1024 * 1024 * 1024 * 1024)) == "1.0 TB"
    assert humanize_bytes(int(1024 * 1024 * 1024 * 1024 * 1024) -
                          1) == "1024.0 TB"
    assert humanize_bytes(int(1024 * 1024 * 1024 * 1024 * 1024)) == "1.0 PB"


def test_humanize_time_delta():
    assert humanize_time_delta(datetime.timedelta(seconds=1)) == "1 second"
    assert humanize_time_delta(datetime.timedelta(seconds=2)) == "2 seconds"
    assert humanize_time_delta(datetime.timedelta(seconds=10)) == "10 seconds"
    assert humanize_time_delta(datetime.timedelta(seconds=59)) == "59 seconds"
    assert humanize_time_delta(datetime.timedelta(seconds=60)) == "1 minute"
    assert humanize_time_delta(datetime.timedelta(seconds=60 *
                                                  2)) == "2 minutes"
    assert humanize_time_delta(datetime.timedelta(seconds=60 * 60 -
                                                  1)) == "59 minutes"
    assert humanize_time_delta(datetime.timedelta(seconds=60 * 60)) == "1 hour"
    assert humanize_time_delta(datetime.timedelta(seconds=60 * 60 *
                                                  2)) == "2 hours"
    assert humanize_time_delta(datetime.timedelta(seconds=60 * 60 *
                                                  24)) == "1 day"
    assert humanize_time_delta(datetime.timedelta(seconds=60 * 60 * 24 *
                                                  2)) == "2 days"
