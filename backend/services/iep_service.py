import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
import json

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except Exception:
    OpenAI = None
    OPENAI_AVAILABLE = False

load_dotenv()


class IEPSummarizer:
    def __init__(self):
        self.model = "gpt-4"
        self.client = None
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            try:
                self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except Exception:
                self.client = None

    def _build_system_prompt(self) -> str:
        return """你是一位专业的自闭症儿童干预专家和个别化教育计划(IEP)协调员。
你的任务是分析团队会议记录，生成专业的IEP进展报告和调整建议。

请重点关注以下内容：
1. 目标行为的进展情况
2. 干预策略的有效性评估
3. 语言治疗师、家长和医生的专业意见
4. 儿童在各领域的发展进展
5. 需要调整的教育计划内容

输出格式要求结构化、专业、具体可操作。"""

    def _build_analysis_prompt(self, transcript: str, child_info: Dict, behavior_history: List[Dict]) -> str:
        child_str = json.dumps(child_info, ensure_ascii=False, indent=2)
        behavior_str = json.dumps(behavior_history, ensure_ascii=False, indent=2)

        return f"""以下是自闭症儿童干预团队会议的完整转写记录：

【儿童基本信息】
{child_str}

【近期行为记录历史】
{behavior_str}

【会议转写记录】
{transcript}

请基于以上信息，生成以下内容：

1. 【会议核心要点摘要】(300-500字)
   - 团队讨论的主要议题
   - 各方达成的共识
   - 存在的争议点

2. 【目标行为进展评估】
   - 列出本次会议讨论的所有目标行为
   - 评估每个目标行为的进展程度(显著进步/有所进步/无明显变化/有所退步)
   - 提供具体的数据支撑

3. 【干预策略分析】
   - 总结当前使用的所有干预策略
   - 评估各策略的有效性
   - 提出需要调整或新增的策略建议

4. 【IEP调整建议】
   - 短期目标调整(未来1-3个月)
   - 长期目标调整(未来6-12个月)
   - 具体的实施计划和时间节点

5. 【各方专业意见整合】
   - 语言治疗师建议
   - 家长反馈与期望
   - 医生的医学建议

请以清晰的Markdown格式输出，确保内容专业、具体、可操作。"""

    def generate_iep_summary(
        self,
        transcript: str,
        child_info: Dict,
        behavior_history: List[Dict]
    ) -> Dict:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": self._build_analysis_prompt(transcript, child_info, behavior_history)}
                ],
                temperature=0.3,
                max_tokens=4000
            )

            summary_content = response.choices[0].message.content

            structured_data = self._extract_structured_data(summary_content)

            return {
                "full_summary": summary_content,
                "structured_data": structured_data
            }

        except Exception as e:
            return {
                "error": f"生成摘要时出错: {str(e)}",
                "full_summary": "",
                "structured_data": {}
            }

    def _extract_structured_data(self, summary_content: str) -> Dict:
        try:
            extraction_prompt = f"""请从以下IEP摘要中提取结构化数据，以JSON格式输出：

{summary_content}

请提取以下字段：
- target_behaviors: 数组，包含所有目标行为名称
- intervention_strategies: 数组，包含所有干预策略
- progress_assessment: 字符串，总体进展评估
- short_term_goals: 数组，短期目标列表
- long_term_goals: 数组，长期目标列表
- key_recommendations: 数组，主要建议列表

只输出JSON，不要其他内容。"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )

            json_str = response.choices[0].message.content.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:-3]
            elif json_str.startswith("```"):
                json_str = json_str[3:-3]

            return json.loads(json_str)

        except Exception as e:
            return {
                "target_behaviors": [],
                "intervention_strategies": [],
                "progress_assessment": "",
                "short_term_goals": [],
                "long_term_goals": [],
                "key_recommendations": []
            }

    def identify_speaker_roles(
        self,
        merged_segments: List[Dict],
        team_members: List[Dict]
    ) -> List[Dict]:
        segments_text = "\n".join([
            f"[{seg['speaker']}] {seg['text']}"
            for seg in merged_segments[:50]
        ])

        roles_prompt = f"""以下是会议记录片段，每个发言都标记了说话人编号(SPEAKER_00, SPEAKER_01等)。

团队成员信息：
{json.dumps(team_members, ensure_ascii=False, indent=2)}

会议记录片段：
{segments_text}

请根据发言内容和专业术语，将每个说话人编号匹配到对应的团队成员角色。

输出JSON格式：
{{
  "SPEAKER_00": {{"name": "姓名", "role": "角色"}},
  "SPEAKER_01": {{"name": "姓名", "role": "角色"}}
}}

只输出JSON，不要其他内容。"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": roles_prompt}],
                temperature=0.1,
                max_tokens=500
            )

            json_str = response.choices[0].message.content.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:-3]
            elif json_str.startswith("```"):
                json_str = json_str[3:-3]

            speaker_mapping = json.loads(json_str)

            for seg in merged_segments:
                if seg["speaker"] in speaker_mapping:
                    seg["speaker_name"] = speaker_mapping[seg["speaker"]]["name"]
                    seg["speaker_role"] = speaker_mapping[seg["speaker"]]["role"]

            return merged_segments

        except Exception as e:
            return merged_segments


iep_summarizer = IEPSummarizer()
