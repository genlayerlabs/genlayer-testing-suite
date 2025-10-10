# {
#   "Seq": [
#     { "Depends": "py-genlayer:1j12s63yfjpva9ik2xgnffgrs6v44y1f52jvj9w7xvdn7qckd379" }
#   ]
# }

import json
from genlayer import *


class MultiAnalysis(gl.Contract):
    """Minimal contract demonstrating multi-analysis pattern"""

    title: str
    goal: str
    last_alignment: u256
    last_quality: u256
    last_engagement: u256
    last_total: u256

    def __init__(self, title: str, goal: str):
        self.title = title
        self.goal = goal
        self.last_alignment = 0
        self.last_quality = 0
        self.last_engagement = 0
        self.last_total = 0

    @gl.public.write
    def analyze_content(self, content: str):
        """Performs multiple sequential analyses on content"""

        # Analysis 1: Content alignment
        alignment_score = self._analyze_alignment(content)

        # Analysis 2: Quality check (only if alignment passes)
        if alignment_score > 0:
            quality_score = self._analyze_quality(content)
        else:
            quality_score = 0

        # Analysis 3: Engagement potential (only if both previous pass)
        if alignment_score > 0 and quality_score > 0:
            engagement_score = self._analyze_engagement(content)
        else:
            engagement_score = 0

        # Calculate total score
        total_score = alignment_score + quality_score + engagement_score

        # Store the results
        self.last_alignment = alignment_score
        self.last_quality = quality_score
        self.last_engagement = engagement_score
        self.last_total = total_score

    def _analyze_alignment(self, content: str) -> int:
        """Analyzes content alignment with goal"""
        task = f"""
        Analyze if this content aligns with the goal: {self.goal}

        Content: {content}

        Respond with JSON:
        {{
            "score": <0-2 where 0=fail, 1=ok, 2=excellent>,
            "reason": <brief explanation>
        }}
        """

        def leader_fn():
            result = gl.nondet.exec_prompt(task)
            parsed = json.loads(result)
            return parsed

        def validator_fn(leaders_res: gl.vm.Result) -> bool:
            validators_res = leader_fn()
            if not isinstance(leaders_res, gl.vm.Return):
                return False
            # Exact match for 0 scores, otherwise allow +/-1
            if validators_res["score"] == 0 or leaders_res.calldata["score"] == 0:
                return validators_res["score"] == leaders_res.calldata["score"]
            return abs(validators_res["score"] - leaders_res.calldata["score"]) <= 1

        analysis = gl.vm.run_nondet(leader_fn, validator_fn)
        return analysis["score"]

    def _analyze_quality(self, content: str) -> int:
        """Analyzes content quality"""
        task = f"""
        Analyze the quality of this content.

        Content: {content}

        Respond with JSON:
        {{
            "score": <0-3 where 0=poor, 1=acceptable, 2=good, 3=excellent>,
            "reason": <brief explanation>
        }}
        """

        def leader_fn():
            result = gl.nondet.exec_prompt(task)
            parsed = json.loads(result)
            return parsed

        def validator_fn(leaders_res: gl.vm.Result) -> bool:
            validators_res = leader_fn()
            if not isinstance(leaders_res, gl.vm.Return):
                return False
            if validators_res["score"] == 0 or leaders_res.calldata["score"] == 0:
                return validators_res["score"] == leaders_res.calldata["score"]
            return abs(validators_res["score"] - leaders_res.calldata["score"]) <= 1

        analysis = gl.vm.run_nondet(leader_fn, validator_fn)
        return analysis["score"]

    def _analyze_engagement(self, content: str) -> int:
        """Analyzes engagement potential"""
        task = f"""
        Analyze the engagement potential of this content for: {self.title}

        Content: {content}

        Respond with JSON:
        {{
            "score": <0-5 where 0=none, 5=excellent>,
            "reason": <brief explanation>
        }}
        """

        def leader_fn():
            result = gl.nondet.exec_prompt(task)
            parsed = json.loads(result)
            return parsed

        def validator_fn(leaders_res: gl.vm.Result) -> bool:
            validators_res = leader_fn()
            if not isinstance(leaders_res, gl.vm.Return):
                return False
            if validators_res["score"] == 0 or leaders_res.calldata["score"] == 0:
                return validators_res["score"] == leaders_res.calldata["score"]
            return abs(validators_res["score"] - leaders_res.calldata["score"]) <= 1

        analysis = gl.vm.run_nondet(leader_fn, validator_fn)
        return analysis["score"]

    @gl.public.view
    def get_last_analysis(self) -> dict:
        """Returns the last analysis results"""
        return {
            "alignment": self.last_alignment,
            "quality": self.last_quality,
            "engagement": self.last_engagement,
            "total": self.last_total
        }

    @gl.public.view
    def get_info(self) -> dict:
        """Returns contract information"""
        return {
            "title": self.title,
            "goal": self.goal
        }
