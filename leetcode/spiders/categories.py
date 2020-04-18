"""
Scrape Leetcode's questions
"""

import json

from scrapy import Request, Spider

from peewee import fn

from leetcode.items import DefaultLoader, Question
from leetcode import models as mod


class LeetcodeCategorySpider(Spider):

    name = "categories"
    allowed_domains = ["leetcode.com"]

    def start_requests(self):
        categories = ["algorithms", "database", "shell", "concurrency"]
        for category in categories:
            url = f"https://leetcode.com/api/problems/{category}"
            headers = {
                "Origin": "https://leetcode.com",
                "Referer": "https://leetcode.com/accounts/login/",
                "X-Requested-With": "XMLHttpRequest",
            }
            yield Request(url, headers=headers, callback=self.parse)

    def parse(self, response):
        data = json.loads(response.body_as_unicode())
        for row in data["stat_status_pairs"]:
            load = DefaultLoader(Question())
            load.add_value("leetcode_id", row["stat"]["question_id"])
            load.add_value("question_id", row["stat"]["question__title_slug"])
            load.add_value("title", row["stat"]["question__title"])
            load.add_value("accepted", row["stat"]["total_acs"])
            load.add_value("submitted", row["stat"]["total_submitted"])
            load.add_value("paid_only", int(row["paid_only"]))
            yield load.load_item()
