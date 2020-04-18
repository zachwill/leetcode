"""
Scrape Leetcode's GraphQL questions endpoint.
"""

import json

from scrapy import Request, Spider

from peewee import fn, JOIN

from leetcode.items import DefaultLoader, Question, Solution, Hint, Tag, SimilarQuestion
from leetcode import models as mod


class LeetcodeQuestionsSpider(Spider):

    name = "questions"
    allowed_domains = ["leetcode.com"]

    def start_requests(self):
        query = (
            mod.Question.select()
            .join(
                mod.Solution,
                JOIN.LEFT_OUTER,
                on=(mod.Question.question_id == mod.Solution.question_id),
            )
            .where(mod.Solution.question_id.is_null())
            .order_by(fn.Random())
            # .limit(50)
        )
        for row in query:
            url = "https://leetcode.com/graphql"
            data = {
                "query": GRAPHQL_QUERY,
                "variables": {"titleSlug": row.question_id},
                "operationName": "getQuestionDetail",
            }
            headers = {
                "Content-Type": "application/json",
                "Origin": "https://leetcode.com",
                "Referer": f"https://leetcode.com/problems/{row.question_id}/description",
                "X-Requested-With": "XMLHttpRequest",
            }
            meta = {"slug": row.question_id}
            yield Request(
                url,
                method="POST",
                body=json.dumps(data),
                headers=headers,
                meta=meta,
                callback=self.parse_graphql,
            )

    def parse_graphql(self, response):
        data = json.loads(response.body_as_unicode())["data"]["question"]

        leetcode_id = data["questionId"]
        question_id = response.meta["slug"]

        load = DefaultLoader(Question())
        load.add_value("leetcode_id", leetcode_id)
        load.add_value("question_id", question_id)
        load.add_value("title", data["title"])
        load.add_value("difficulty", data["difficulty"])
        load.add_value("likes", data["likes"])
        load.add_value("dislikes", data["dislikes"])
        load.add_value("content", data["content"])
        load.add_value("paid_only", int(data["isPaidOnly"]))
        load.add_value("sample_test_case", data["sampleTestCase"])

        data["stats"] = json.loads(data["stats"])
        data["similarQuestions"] = json.loads(data["similarQuestions"])

        load.add_value("accepted", data["stats"]["totalAcceptedRaw"])
        load.add_value("submitted", data["stats"]["totalSubmissionRaw"])
        load.add_value("accepted_rate", data["stats"]["acRate"], re="(.+)%")

        yield load.load_item()

        for similar in data["similarQuestions"]:
            load_similar = DefaultLoader(SimilarQuestion())
            load_similar.add_value("leetcode_id", leetcode_id)
            load_similar.add_value("question_id", question_id)
            load_similar.add_value("similar_id", similar["titleSlug"])
            load_similar.add_value("similar_title", similar["title"])
            load_similar.add_value("similar_difficulty", similar["difficulty"])
            yield load_similar.load_item()

        for tag in data["topicTags"]:
            load_tag = DefaultLoader(Tag())
            load_tag.add_value("leetcode_id", leetcode_id)
            load_tag.add_value("question_id", question_id)
            load_tag.add_value("tag_id", tag["slug"])
            load_tag.add_value("tag_name", tag["name"])
            yield load_tag.load_item()

        for hint in data["hints"]:
            load_hint = DefaultLoader(Hint())
            load_hint.add_value("leetcode_id", leetcode_id)
            load_hint.add_value("question_id", question_id)
            load_hint.add_value("hint", hint)
            yield load_hint.load_item()

        if not data["solution"]:
            return

        load_solution = DefaultLoader(Solution())
        load_solution.add_value("leetcode_id", leetcode_id)
        load_solution.add_value("question_id", question_id)

        load_solution.add_value("url", data["solution"].get("url"))
        load_solution.add_value("content", data["solution"].get("content"))
        load_solution.add_value("visible", int(data["solution"].get("canSeeDetail")))

        if "rating" in data["solution"] and data["solution"]["rating"]:
            load_solution.add_value("rating", data["solution"]["rating"].get("average"))
            load_solution.add_value(
                "rating_count", data["solution"]["rating"].get("count")
            )

        yield load_solution.load_item()


GRAPHQL_QUERY = """
query getQuestionDetail($titleSlug : String!) {
  question(titleSlug: $titleSlug) {
    questionId
    questionFrontendId
    title
    content
    stats
    difficulty
    isPaidOnly
    sampleTestCase
    enableRunCode
    translatedContent

    likes
    dislikes
    similarQuestions
    topicTags {
      name
      slug
    }
    stats

    hints
    solution {
      id
      url
      content
      contentTypeId
      canSeeDetail
      rating {
        id
        count
        average
      }
    }
  }
}
""".strip()
