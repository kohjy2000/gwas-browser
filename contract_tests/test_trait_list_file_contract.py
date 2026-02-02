import json
import os


def test_trait_list_files_exist_and_have_expected_schema():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    trait_list_path = os.path.join(project_root, "data", "trait_list.json")
    meta_path = os.path.join(project_root, "data", "trait_list.meta.json")

    assert os.path.exists(trait_list_path)
    assert os.path.exists(meta_path)

    with open(trait_list_path, "r", encoding="utf-8") as f:
        traits = json.load(f)

    assert isinstance(traits, list)
    assert traits
    for item in traits:
        assert isinstance(item, dict)
        assert "trait" in item
        assert "shortForm" in item
        assert "uri" in item
        assert isinstance(item["trait"], str)
        assert isinstance(item["shortForm"], str)
        assert isinstance(item["uri"], str)

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert isinstance(meta, dict)
    assert "updated_at" in meta
    assert "total_traits" in meta
    assert isinstance(meta["updated_at"], str)
    assert isinstance(meta["total_traits"], int)
    assert meta["total_traits"] == len(traits)
