import os
import os.path

from cromwellhelper.fileutils import *


def test_readlink_abs():
    testfiles_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                 "testfiles", "link")
    expected = os.path.join(testfiles_dir, "a", "one")

    assert expected == readlink_abs(os.path.join(testfiles_dir, "a", "two"))


def test_realpath():
    testfiles_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                 "testfiles", "link")
    expected = os.path.join(testfiles_dir, "a", "one")

    assert expected == realpath(expected)
    assert expected == realpath(os.path.join(testfiles_dir, "b", "six"))
    assert expected == realpath(os.path.join(testfiles_dir, "c", "six"))
    assert expected == realpath(os.path.join(testfiles_dir, "d", "one"))


def test_create_relative_symlink(tmpdir):
    os.makedirs(os.path.join(tmpdir, "c"), exist_ok=True)

    create_relative_symlink(os.path.join(tmpdir, "a"),
                            os.path.join(tmpdir, "b"))
    assert os.path.islink(os.path.join(tmpdir, "b"))
    assert "a" == os.readlink(os.path.join(tmpdir, "b"))

    create_relative_symlink(os.path.join(tmpdir, "c", "a"),
                            os.path.join(tmpdir, "d"))
    assert os.path.islink(os.path.join(tmpdir, "d"))
    assert "c/a" == os.readlink(os.path.join(tmpdir, "d"))

    create_relative_symlink(os.path.join(tmpdir, "d"),
                            os.path.join(tmpdir, "c", "f"))
    assert os.path.islink(os.path.join(tmpdir, "c", "f"))
    assert "../d" == os.readlink(os.path.join(tmpdir, "c", "f"))


def test_search_symlinks():
    testfiles_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                 "testfiles", "link")

    link_list = [(os.path.relpath(x[0], testfiles_dir),
                  os.path.relpath(x[1], testfiles_dir),
                  os.path.relpath(x[2], testfiles_dir))
                 for x in search_symlinks(testfiles_dir)]
    link_list.sort()

    assert link_list == [
        ('a/two', 'a/one', 'a/one'),
        ('b/five', 'b/three', 'a/one'),
        ('b/four', 'a/two', 'a/one'),
        ('b/six', 'b/four', 'a/one'),
        ('b/three', 'a/one', 'a/one'),
    ]
