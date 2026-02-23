from __future__ import annotations

from glsim.genvm_stubs import _VecDB


def test_vecdb_knn_basic():
    db = _VecDB()
    db.insert([0.0, 0.0], "a")
    db.insert([1.0, 1.0], "b")

    result = db.knn([0.1, 0.1], k=1)
    assert len(result) == 1
    assert result[0].value == "a"


def test_vecdb_survives_missing_private_entries_after_restore():
    db = _VecDB()
    db.insert([0.0, 0.0], "a")

    # Simulate deserialization path that keeps public attrs but drops `_entries`.
    restored = _VecDB.__new__(_VecDB)
    restored.entries = list(db.entries)

    restored.insert([2.0, 2.0], "b")
    result = restored.knn([1.9, 1.9], k=2)
    assert len(result) == 2
    assert result[0].value == "b"
