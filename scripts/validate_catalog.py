"""Validate catalog integrity and prevent accidentally packaging source catalogs."""
import json
import pathlib
import re

root = pathlib.Path(__file__).resolve().parents[1]
dist = root / "docs"
products = json.loads((dist / "data/products.json").read_text()) + json.loads((dist / "data/autoparts.json").read_text()) + json.loads((dist / "data/tires.json").read_text()) + json.loads((dist / "data/jewelry.json").read_text()) + json.loads((dist / "data/bathroom.json").read_text())
ids = [p["id"] for p in products]
assert len(ids) == len(set(ids)), "Duplicate product identifiers"
assert products, "Catalog must contain products"
allowed = {"id", "title", "category", "subcategory", "collection", "collectionName", "description", "image", "images", "specs", "tags", "searchTerms", "sourceRevision", "imageQualityNote", "imageIndex"}
for product in products:
    assert set(product) <= allowed, (product["id"], "Unapproved public field")
    assert re.fullmatch(r"FK-[A-Z]\d{3,8}", product["id"])
    assert re.fullmatch(r"FK-C\d{2,5}", product["collection"])
    assert product["title"] and product["category"] and product["subcategory"]
    images = product["images"]
    if images:
        for image in images:
            assert re.fullmatch(r"assets/products/[a-z0-9-]+\.(?:webp|png)", image)
            assert (dist / image).is_file(), image
        assert product["image"] in images
        if "imageIndex" in product:
            assert isinstance(product["imageIndex"], int)
            if product["category"] == "Автозапчасти":
                assert product["image"] == "assets/products/geely-sc7-engine-atlas.png"
                assert 0 <= product["imageIndex"] < 56
            elif product["category"] == "Шины":
                assert product["image"] == "assets/products/tires-patterns-atlas.webp"
                assert 0 <= product["imageIndex"] < 73
            elif product["category"] == "Ванная":
                assert re.fullmatch(r"assets/products/bathroom-photos-\d{3}\.webp", product["image"])
                assert 0 <= product["imageIndex"] < 16
            elif product["category"] == "Бижутерия":
                assert re.fullmatch(r"assets/products/jewelry-photos-\d{3}\.webp", product["image"])
                assert 0 <= product["imageIndex"] < 16
            else:
                raise AssertionError("Unsupported atlas category")
    else:
        assert product["category"] == "Автозапчасти" and product["image"] == "", "Missing photo allowed only during image transfer"
    text = json.dumps(product, ensure_ascii=False)
    assert not re.search(r"https?://|@|[\u3400-\u9fff]|\.pdf|\.xlsx", text), (product["id"], "Source identity or external link")
for path in dist.rglob("*"):
    if not path.is_file():
        continue
    assert path.suffix.lower() not in {".pdf", ".xlsx", ".xls", ".csv"}, "Source file in published folder"
    assert not re.search(r"private|supplier|original|source-map|stroller-2023", str(path.relative_to(dist)), re.I), "Internal file in published folder"
    if path.suffix in {".webp", ".png"}:
        from PIL import Image
        with Image.open(path) as im:
            assert not im.getexif(), "Image contains EXIF"
            assert "xmp" not in im.info, "Image contains XMP"
print(f"Validated {len(products)} public records and {len(list((dist/'assets/products').glob('*.webp')))} images.")
