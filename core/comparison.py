# -*- coding: utf-8 -*-
"""محرك مقارنة بين فصلين دراسيين (أو ملفين مختلفين) لنفس الطلاب."""
import statistics


class ComparisonResult:
    """
    يقارن بين تحليلين (AnalysisResult) — عادة فصل أول وفصل ثاني لنفس الصف —
    ويطابق الطلاب بالهوية أولًا (أدق)، وبالاسم العربي كاحتياط لو الهوية غير متوفرة.
    """
    def __init__(self, analysis_before, analysis_after,
                 label_before="الفصل الأول", label_after="الفصل الثاني"):
        self.analysis_before = analysis_before
        self.analysis_after = analysis_after
        self.label_before = label_before
        self.label_after = label_after
        self._build()

    def _index_by_id_or_name(self, analysis):
        by_id = {}
        by_name = {}
        for s in analysis.students:
            sid = s.get("id")
            if sid:
                by_id[str(sid)] = s
            by_name[s["name_ar"]] = s
        return by_id, by_name

    def _build(self):
        before_by_id, before_by_name = self._index_by_id_or_name(self.analysis_before)
        after_by_id, after_by_name = self._index_by_id_or_name(self.analysis_after)

        matched = []
        unmatched_after = []
        matched_after_keys = set()

        for s_before in self.analysis_before.students:
            sid = str(s_before.get("id")) if s_before.get("id") else None
            s_after = None
            if sid and sid in after_by_id:
                s_after = after_by_id[sid]
                matched_after_keys.add(("id", sid))
            elif s_before["name_ar"] in after_by_name:
                s_after = after_by_name[s_before["name_ar"]]
                matched_after_keys.add(("name", s_before["name_ar"]))

            if s_after is not None:
                diff = round(s_after["average"] - s_before["average"], 2)
                matched.append({
                    "name_ar": s_before["name_ar"],
                    "class_before": s_before.get("class"),
                    "class_after": s_after.get("class"),
                    "avg_before": s_before["average"],
                    "avg_after": s_after["average"],
                    "diff": diff,
                    "grade_before": s_before.get("general_grade"),
                    "grade_after": s_after.get("general_grade"),
                })

        for s_after in self.analysis_after.students:
            sid = str(s_after.get("id")) if s_after.get("id") else None
            key_id = ("id", sid) if sid else None
            key_name = ("name", s_after["name_ar"])
            if key_id in matched_after_keys or key_name in matched_after_keys:
                continue
            unmatched_after.append(s_after)

        unmatched_before = [
            s for s in self.analysis_before.students
            if s["name_ar"] not in {m["name_ar"] for m in matched}
        ]

        self.matched = sorted(matched, key=lambda m: m["diff"], reverse=True)
        self.unmatched_before = unmatched_before
        self.unmatched_after = unmatched_after
        self.matched_count = len(matched)

        diffs = [m["diff"] for m in matched]
        self.overall_diff = round(statistics.mean(diffs), 2) if diffs else 0
        self.improved = [m for m in self.matched if m["diff"] > 1]
        self.declined = [m for m in self.matched if m["diff"] < -1]
        self.stable = [m for m in self.matched if -1 <= m["diff"] <= 1]

        self.most_improved = sorted(self.matched, key=lambda m: m["diff"], reverse=True)[:10]
        self.most_declined = sorted(self.matched, key=lambda m: m["diff"])[:10]

        # مقارنة متوسط كل فصل بين الفترتين
        self.class_comparison = {}
        before_classes = self.analysis_before.class_stats
        after_classes = self.analysis_after.class_stats
        all_class_keys = set(before_classes.keys()) | set(after_classes.keys())
        for cls in all_class_keys:
            b = before_classes.get(cls, {}).get("mean")
            a = after_classes.get(cls, {}).get("mean")
            self.class_comparison[cls] = {
                "before": b, "after": a,
                "diff": round(a - b, 2) if (a is not None and b is not None) else None,
            }
