#!/usr/bin/env python3
"""
バッチ10-18のスキーマを標準形式に変換
"""
import json

# 元のデータ（エージェントから取得）
raw_data = {
  "respondents": [
    {
      "respondent_id": 10,
      "story_title": "CX通信 19-6] 魔法の絵の具と大きなカバン",
      "demographics": {"gender": "男性", "age_group": "50代"},
      "ratings": {
        "overall_evaluation": {"emotional_resonance": 4, "story_flow": 3, "recommend_to_others": 3},
        "story_immersion": {"character_empathy": 3},
        "customer_awareness": {"reflects_service_quality": 4, "character_interaction_resonance": 4},
        "behavioral_intention": {"change_response_quality": 4, "continue_with_confidence": 4, "specific_behavior_change": ""},
        "adoption_recommendation": 8,
        "job_relevance": 2
      },
      "free_response": {"unnatural_parts": "", "obstacles_to_practice": "", "important_messages": ""}
    },
    {
      "respondent_id": 11,
      "story_title": "CX通信 19-7] 机の上の太陽",
      "demographics": {"gender": "男性", "age_group": "50代"},
      "ratings": {
        "overall_evaluation": {"emotional_resonance": 4, "story_flow": 2, "recommend_to_others": 2},
        "story_immersion": {"character_empathy": 1},
        "customer_awareness": {"reflects_service_quality": 3, "character_interaction_resonance": 2},
        "behavioral_intention": {"change_response_quality": 2, "continue_with_confidence": 2, "specific_behavior_change": ""},
        "adoption_recommendation": 3,
        "job_relevance": 4
      },
      "free_response": {"unnatural_parts": "", "obstacles_to_practice": "", "important_messages": ""}
    },
    {
      "respondent_id": 12,
      "story_title": "CX通信 19-15] 完璧な準備",
      "demographics": {"gender": "男性", "age_group": "50代"},
      "ratings": {
        "overall_evaluation": {"emotional_resonance": 3, "story_flow": 3, "recommend_to_others": 3},
        "story_immersion": {"character_empathy": 3},
        "customer_awareness": {"reflects_service_quality": 3, "character_interaction_resonance": 3},
        "behavioral_intention": {"change_response_quality": 3, "continue_with_confidence": 3, "specific_behavior_change": ""},
        "adoption_recommendation": 6,
        "job_relevance": 2
      },
      "free_response": {"unnatural_parts": "", "obstacles_to_practice": "", "important_messages": ""}
    },
    {
      "respondent_id": 13,
      "story_title": "CX通信 19-6] 魔法の絵の具と大きなカバン",
      "demographics": {"gender": "男性", "age_group": "50代"},
      "ratings": {
        "overall_evaluation": {"emotional_resonance": 3, "story_flow": 3, "recommend_to_others": 3},
        "story_immersion": {"character_empathy": 4},
        "customer_awareness": {"reflects_service_quality": 3, "character_interaction_resonance": 4},
        "behavioral_intention": {"change_response_quality": 4, "continue_with_confidence": 3, "specific_behavior_change": "相手を思いやる心"},
        "adoption_recommendation": 7,
        "job_relevance": 3
      },
      "free_response": {"unnatural_parts": "", "obstacles_to_practice": "", "important_messages": ""}
    },
    {
      "respondent_id": 14,
      "story_title": "CX通信 19-7] 机の上の太陽",
      "demographics": {"gender": "男性", "age_group": "50代"},
      "ratings": {
        "overall_evaluation": {"emotional_resonance": 3, "story_flow": 3, "recommend_to_others": 3},
        "story_immersion": {"character_empathy": 4},
        "customer_awareness": {"reflects_service_quality": 3, "character_interaction_resonance": 4},
        "behavioral_intention": {"change_response_quality": 4, "continue_with_confidence": 3, "specific_behavior_change": "相手を思いやる心"},
        "adoption_recommendation": 7,
        "job_relevance": 3
      },
      "free_response": {"unnatural_parts": "", "obstacles_to_practice": "", "important_messages": ""}
    },
    {
      "respondent_id": 15,
      "story_title": "CX通信 19-15] 完璧な準備",
      "demographics": {"gender": "男性", "age_group": "50代"},
      "ratings": {
        "overall_evaluation": {"emotional_resonance": 3, "story_flow": 3, "recommend_to_others": 3},
        "story_immersion": {"character_empathy": 3},
        "customer_awareness": {"reflects_service_quality": 3, "character_interaction_resonance": 3},
        "behavioral_intention": {"change_response_quality": 4, "continue_with_confidence": 3, "specific_behavior_change": "相手を思いやる心"},
        "adoption_recommendation": 7,
        "job_relevance": 3
      },
      "free_response": {"unnatural_parts": "", "obstacles_to_practice": "", "important_messages": ""}
    },
    {
      "respondent_id": 16,
      "story_title": "CX通信 19-6] 魔法の絵の具と大きなカバン",
      "demographics": {"gender": "男性", "age_group": "40代"},
      "ratings": {
        "overall_evaluation": {"emotional_resonance": 2, "story_flow": 2, "recommend_to_others": 2},
        "story_immersion": {"character_empathy": 2},
        "customer_awareness": {"reflects_service_quality": 2, "character_interaction_resonance": 2},
        "behavioral_intention": {"change_response_quality": 2, "continue_with_confidence": 2, "specific_behavior_change": "がんばる人々"},
        "adoption_recommendation": 5,
        "job_relevance": 3
      },
      "free_response": {"unnatural_parts": "", "obstacles_to_practice": "", "important_messages": ""}
    },
    {
      "respondent_id": 17,
      "story_title": "CX通信 19-7] 机の上の太陽",
      "demographics": {"gender": "男性", "age_group": "40代"},
      "ratings": {
        "overall_evaluation": {"emotional_resonance": 2, "story_flow": 2, "recommend_to_others": 2},
        "story_immersion": {"character_empathy": 2},
        "customer_awareness": {"reflects_service_quality": 2, "character_interaction_resonance": 2},
        "behavioral_intention": {"change_response_quality": 2, "continue_with_confidence": 2, "specific_behavior_change": "がんがしやんる"},
        "adoption_recommendation": 6,
        "job_relevance": 2
      },
      "free_response": {"unnatural_parts": "", "obstacles_to_practice": "", "important_messages": ""}
    },
    {
      "respondent_id": 18,
      "story_title": "CX通信 19-15] 完璧な準備",
      "demographics": {"gender": "男性", "age_group": "40代"},
      "ratings": {
        "overall_evaluation": {"emotional_resonance": 2, "story_flow": 2, "recommend_to_others": 2},
        "story_immersion": {"character_empathy": 2},
        "customer_awareness": {"reflects_service_quality": 2, "character_interaction_resonance": 2},
        "behavioral_intention": {"change_response_quality": 3, "continue_with_confidence": 3, "specific_behavior_change": "がんがしやんる"},
        "adoption_recommendation": 6,
        "job_relevance": 3
      },
      "free_response": {"unnatural_parts": "", "obstacles_to_practice": "", "important_messages": ""}
    }
  ]
}

# 標準形式に変換
converted = {"respondents": []}

for r in raw_data["respondents"]:
    converted_r = {
        "respondent_id": r["respondent_id"],
        "source_pages": [f"page_{(r['respondent_id']-1)*2+1:03d}.png", f"page_{(r['respondent_id']-1)*2+2:03d}.png"],
        "story_title": r["story_title"].replace("] ", " "),
        "gender": r["demographics"]["gender"],
        "age_group": r["demographics"]["age_group"],
        "Q1_inspiring": r["ratings"]["overall_evaluation"]["emotional_resonance"],
        "Q2_story_flow": r["ratings"]["overall_evaluation"]["story_flow"],
        "Q3_recommend_others": r["ratings"]["overall_evaluation"]["recommend_to_others"],
        "Q4_character_empathy": r["ratings"]["story_immersion"]["character_empathy"],
        "Q5_cx_reflection": r["ratings"]["customer_awareness"]["reflects_service_quality"],
        "Q6_compassion_empathy": r["ratings"]["customer_awareness"]["character_interaction_resonance"],
        "Q7_want_to_change": r["ratings"]["behavioral_intention"]["change_response_quality"],
        "Q8_continue_with_confidence": r["ratings"]["behavioral_intention"]["continue_with_confidence"],
        "Q9_specific_action_text": r["ratings"]["behavioral_intention"]["specific_behavior_change"] or None,
        "Q10_nps": r["ratings"]["adoption_recommendation"],
        "Q11_not_applicable": r["ratings"]["job_relevance"],
        "Q12_insights_unnatural": r["free_response"]["unnatural_parts"] or None,
        "Q13_barriers_to_practice": r["free_response"]["obstacles_to_practice"] or None,
        "Q14_other_cx_importance": r["free_response"]["important_messages"] or None
    }
    converted["respondents"].append(converted_r)

# 保存
with open("../output/batch_10_18.json", "w", encoding="utf-8") as f:
    json.dump(converted, f, indent=2, ensure_ascii=False)

print("✅ バッチ10-18を標準形式に変換して保存しました")
print(f"   回答者数: {len(converted['respondents'])}")
