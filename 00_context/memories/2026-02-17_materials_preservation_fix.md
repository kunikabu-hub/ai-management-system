# 追加質問後のMaterials保持問題の修正

**日時**: 2026年2月17日
**問題**: 追加質問に回答しても生成結果に反映されない
**原因**: complete_story_generation が materials を毎回再生成していた

---

## 問題の詳細

### 症状
- ユーザーが追加質問に回答
- APIログには「✅ Materials updated: 4 episodes」と表示
- しかし実際の session ファイルには 2 episodes のまま
- 生成された脚本にも追加情報が反映されない

### 根本原因

**answer_additional_questions のフロー**:
1. 追加質問の回答を受け取る
2. episodes に手動で新しいエピソードを追加
3. `sess["materials"]` を更新して保存 → ✅ ここまでは正常
4. `sess["additional_questions_answered"] = True` をセット

**complete_story_generation の問題**:
```python
# 修正前（問題のあるコード）
def complete_story_generation(user_id: str, ...):
    # Step 1: materials生成
    materials = get_materials(user_id)  # ❌ 毎回再生成！
    # ↑ これが会話ログから materials を再生成
    # → 手動追加したepisodesが消える
```

`get_materials()` 関数は会話ログ全体を AI で分析して materials を生成するが:
- 追加質問の回答は `messages` に追加されている
- しかし AI は元のインタビュー内容と同じように判断してしまう
- 結果として同じ 2 episodes しか生成されない
- 手動で追加した 2 episodes は上書きされて消える

---

## 修正内容

### コード変更

**ファイル**: `tools/memoir_editor_api.py`
**関数**: `complete_story_generation`
**行番号**: 1178-1186

```python
# 修正後
if sess.get("materials") and sess.get("additional_questions_answered"):
    # 追加質問回答済みの場合は既存materialsを使用
    print(f"📦 Step 1/4: Using existing materials (additional questions answered)...")
    materials = sess["materials"]
    result["materials"] = materials
    result["steps_completed"].append("materials")
    print(f"✅ Using existing materials: {len(materials.get('episodes', []))} episodes, {len(materials.get('timeline', []))} timeline")
else:
    # 通常フロー：materialsを再生成
    print(f"📦 Step 1/4: Generating materials for {user_id}...")
    materials = get_materials(user_id)
    result["materials"] = materials
    result["steps_completed"].append("materials")
    print("✅ Materials generated")
```

### 修正のポイント

1. **条件判定を追加**:
   - `sess.get("materials")` が存在 AND
   - `sess.get("additional_questions_answered")` が True

2. **既存 materials を使用**:
   - 条件を満たす場合、`get_materials()` を呼ばずに既存の materials を使用
   - これにより手動追加した episodes が保持される

3. **ログ出力を改善**:
   - どちらのパスを通ったか明確にログ出力
   - episodes 数と timeline 数を表示

---

## 動作確認

### テストフロー

1. **初期状態**: episodes 2件
2. **追加質問回答**: episodes を 4件に増やす（手動追加）
3. **complete_story_generation 実行**:
   - 修正前: episodes が 2件に戻る ❌
   - 修正後: episodes が 4件のまま ✅

### ログ出力（修正後）

```
📦 Step 1/4: Using existing materials (additional questions answered)...
✅ Using existing materials: 4 episodes, 2 timeline
✅ Additional questions already answered, skipping insufficiency check
📖 Step 2/4: Generating story for user_001...
✅ Story generated
```

### API レスポンス

```json
{
  "success": true,
  "materials_summary": {
    "episodes_count": 4,  // ✅ 4件保持されている
    "timeline_count": 2
  },
  "story_summary": {
    "title": "ポラーとの日々",
    "chapters": 5
  }
}
```

---

## 影響範囲

### 変更による影響

**✅ 改善されること**:
- 追加質問の回答が正しく materials に反映される
- 生成される脚本により多くの情報が含まれる
- 葛藤（谷）や具体的な情景が脚本に反映される

**🔒 影響を受けないこと**:
- 初回のインタビュー → materials 生成フロー（従来通り）
- 追加質問に答えていない場合の動作（従来通り）

### 後方互換性

- `additional_questions_answered` フラグがない既存セッションでも正常動作
- 条件判定で `sess.get("additional_questions_answered")` を使用しているため、フラグがない場合は False として扱われる

---

## 今後の改善案

### 1. AI による materials 更新

現在は手動で episodes を追加しているが、将来的には:
```python
# 追加質問の回答を含めて materials を再生成
materials = regenerate_materials_with_additional_info(user_id, existing_materials, additional_answers)
```

### 2. Incremental Update

既存 materials に追加情報だけをマージ:
```python
updated_materials = merge_additional_info(existing_materials, additional_answers)
```

### 3. Materials のバージョン管理

```python
sess["materials_history"] = [
    {"version": 1, "timestamp": "...", "materials": {...}},
    {"version": 2, "timestamp": "...", "materials": {...}}
]
```

---

## 関連ファイル

- **API**: `tools/memoir_editor_api.py`
- **UI**: `tools/test_ui_v3.html`
- **セッション**: `tools/sessions/user_001.json`
- **ログ**: `/tmp/memoir_integrated.log`

---

## まとめ

**修正前の問題**:
- 追加質問 → 回答 → 保存 ✅
- complete_story_generation → materials 再生成 → 上書き ❌

**修正後の動作**:
- 追加質問 → 回答 → 保存 ✅
- complete_story_generation → 既存 materials 使用 ✅
- 脚本生成で追加情報を活用 ✅

これにより、ユーザーが追加質問に丁寧に答えた内容が、最終的な脚本に正しく反映されるようになりました。
