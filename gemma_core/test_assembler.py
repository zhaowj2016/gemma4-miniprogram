"""Unit tests for the semantic block assembler."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from assembler import assemble


class AssemblerTests(unittest.TestCase):
    def test_two_block_classes_do_not_collide(self) -> None:
        page = assemble(["HeroBanner", "ProductList"])

        self.assertIn("hero-banner__title", page["wxml"])
        self.assertIn("product-list__title", page["wxml"])
        self.assertIn(".hero-banner__title", page["wxss"])
        self.assertIn(".product-list__title", page["wxss"])

    def test_data_keys_merge_without_overwrite(self) -> None:
        page = assemble(
            [
                {
                    "name": "BlockA",
                    "wxml": "<view class=\"block-a\"><text>{{title}}</text></view>",
                    "wxss": ".block-a { padding: 10rpx; }",
                    "data": {"title": "First"},
                    "methods": {},
                },
                {
                    "name": "BlockB",
                    "wxml": "<view class=\"block-b\"><text>{{title}}</text></view>",
                    "wxss": ".block-b { padding: 12rpx; }",
                    "data": {"title": "Second"},
                    "methods": {},
                },
            ]
        )

        self.assertIn('"title": "First"', page["js"])
        self.assertIn('"BlockB_title": "Second"', page["js"])
        self.assertIn("{{BlockB_title}}", page["wxml"])

    def test_duplicate_handler_is_renamed_in_second_block(self) -> None:
        page = assemble(
            [
                {
                    "name": "FirstAction",
                    "wxml": "<view class=\"first-action\"><button bindtap=\"onTap\">A</button></view>",
                    "wxss": ".first-action { margin: 8rpx; }",
                    "data": {},
                    "methods": {"onTap": "function() { this.setData({ firstDone: true }); }"},
                },
                {
                    "name": "SecondAction",
                    "wxml": "<view class=\"second-action\"><button bindtap=\"onTap\">B</button></view>",
                    "wxss": ".second-action { margin: 8rpx; }",
                    "data": {},
                    "methods": {"onTap": "function() { this.setData({ secondDone: true }); }"},
                },
            ]
        )

        self.assertIn("bindtap=\"onTap\"", page["wxml"])
        self.assertIn("bindtap=\"SecondAction_onTap\"", page["wxml"])
        self.assertIn("onTap: function()", page["js"])
        self.assertIn("SecondAction_onTap: function()", page["js"])


if __name__ == "__main__":
    unittest.main()
