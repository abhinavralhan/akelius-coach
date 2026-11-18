"""Run: python -m unittest tests.test_videos  (no network: YouTube is faked)"""
import unittest

from coach.videos import top_videos


def fake_get(url):
    if "oembed" in url:
        if "BBBBBBBBBBB" in url:
            raise OSError("404: private or removed")
        return {"title": "Real title from YouTube", "author_name": "Some Channel"}
    return {"items": [{"id": {"videoId": "AAAAAAAAAAA"}}, {"id": {"videoId": "BBBBBBBBBBB"}},
                      {"id": {"videoId": "bad id <script>"}}, {"id": {"videoId": "CCCCCCCCCCC"}},
                      {"id": {"videoId": "DDDDDDDDDDD"}}, {"id": {"videoId": "EEEEEEEEEEE"}}]}


class VideosTest(unittest.TestCase):
    def test_keeps_three_confirmed_videos_and_skips_bad_ones(self):
        v = top_videos("Dividing fractions", 6, "k", get=fake_get)
        self.assertEqual([x["url"][-11:] for x in v], ["AAAAAAAAAAA", "CCCCCCCCCCC", "DDDDDDDDDDD"])
        self.assertEqual(v[0]["title"], "Real title from YouTube")


if __name__ == "__main__":
    unittest.main()
