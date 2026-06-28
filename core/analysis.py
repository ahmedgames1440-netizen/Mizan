# -*- coding: utf-8 -*-
"""محرك التحليل الإحصائي — يبني كل المؤشرات والرسوم من بيانات الطلاب المستخرجة."""
from collections import defaultdict
import statistics

NON_ACADEMIC_SUBJECTS = {"المواظبة", "السلوك", "النشاط"}


class AnalysisResult:
    def __init__(self, students, risk_threshold=65.0):
        self.students = [s for s in students if s.get("average") is not None]
        self.risk_threshold = risk_threshold
        self._build()

    def _build(self):
        avgs = [s["average"] for s in self.students]
        self.count = len(self.students)
        self.overall_average = round(statistics.mean(avgs), 2) if avgs else 0
        self.highest = max(self.students, key=lambda s: s["average"]) if self.students else None
        self.lowest = min(self.students, key=lambda s: s["average"]) if self.students else None

        # توزيع التقديرات
        grade_counts = defaultdict(int)
        for s in self.students:
            g = s.get("general_grade") or "غير محدد"
            grade_counts[g] += 1
        self.grade_distribution = dict(grade_counts)

        # مقارنة الفصول
        class_groups = defaultdict(list)
        for s in self.students:
            cls = s.get("class") or "غير محدد"
            class_groups[cls].append(s["average"])
        self.class_stats = {}
        for cls, vals in class_groups.items():
            self.class_stats[cls] = {
                "mean": round(statistics.mean(vals), 2),
                "min": round(min(vals), 2),
                "max": round(max(vals), 2),
                "count": len(vals),
            }

        # متوسط كل مادة (نستبعد غير الأكاديمية اختياريًا في العرض، لكن نحتفظ بكل البيانات)
        subj_groups = defaultdict(list)
        for s in self.students:
            for sub in s.get("subjects", []):
                if sub.get("total_pct") is not None:
                    subj_groups[sub["subject_ar"]].append(sub["total_pct"])
        self.subject_averages = {
            subj: round(statistics.mean(vals), 2)
            for subj, vals in subj_groups.items()
        }
        self.subject_averages_academic_only = {
            k: v for k, v in self.subject_averages.items() if k not in NON_ACADEMIC_SUBJECTS
        }

        # الطلاب المعرضون للخطر
        self.at_risk = sorted(
            [s for s in self.students if s["average"] < self.risk_threshold],
            key=lambda s: s["average"]
        )
        # قائمة متابعة وقائية (أدنى 15 معدلاً حتى لو ما تحت الحد)
        self.watch_list = sorted(self.students, key=lambda s: s["average"])[:15]

        # الغياب
        absences = [s["absence"] for s in self.students if s.get("absence") is not None]
        self.avg_absence = round(statistics.mean(absences), 2) if absences else 0
        self.max_absence = max(absences) if absences else 0

        # ترتيب الفصول من الأفضل للأضعف
        self.class_ranking = sorted(
            self.class_stats.items(), key=lambda kv: kv[1]["mean"], reverse=True
        )

        # أفضل وأضعف المواد
        if self.subject_averages_academic_only:
            sorted_subjects = sorted(self.subject_averages_academic_only.items(), key=lambda kv: kv[1])
            self.weakest_subjects = sorted_subjects[:5]
            self.strongest_subjects = sorted_subjects[-5:][::-1]
        else:
            self.weakest_subjects = []
            self.strongest_subjects = []

        # كشف ارتباط الغياب بالمعدل (بسيط)
        self.absence_correlation_note = self._absence_insight()

        # كشف الحالات الشاذة (تفاوت كبير وغير متوقع بمادة معينة)
        self.anomalies = self._detect_anomalies()

    def _detect_anomalies(self, min_gap=25.0):
        """
        يكشف الطلاب الذين لديهم تفاوت كبير وغير متوقع بمادة معينة مقارنة
        بمتوسط أدائهم الشخصي بباقي المواد. هذا غالبًا يشير إلى: خطأ محتمل
        بإدخال الدرجة، فجوة تعليمية محددة بمادة واحدة، أو حالة تحتاج انتباه
        من المعلم. min_gap: الحد الأدنى للفرق (بالنقاط) لاعتباره شاذًا.
        يُرجع حالة واحدة فقط لكل طالب (الأكبر فرقًا)، وليس كل المواد الشاذة.
        """
        per_student_best = {}
        for s in self.students:
            subjects = [sub for sub in s.get("subjects", [])
                        if sub.get("total_pct") is not None and sub["subject_ar"] not in NON_ACADEMIC_SUBJECTS]
            if len(subjects) < 3:
                continue

            best_anomaly = None
            for sub in subjects:
                others = [o["total_pct"] for o in subjects if o["subject_ar"] != sub["subject_ar"]]
                if not others:
                    continue
                personal_avg = statistics.mean(others)
                gap = sub["total_pct"] - personal_avg
                if abs(gap) >= min_gap:
                    candidate = {
                        "student": s,
                        "subject": sub["subject_ar"],
                        "subject_pct": sub["total_pct"],
                        "personal_avg": round(personal_avg, 1),
                        "gap": round(gap, 1),
                        "direction": "drop" if gap < 0 else "spike",
                    }
                    if best_anomaly is None or abs(gap) > abs(best_anomaly["gap"]):
                        best_anomaly = candidate

            if best_anomaly:
                per_student_best[s["name_ar"]] = best_anomaly

        anomalies = list(per_student_best.values())
        anomalies.sort(key=lambda a: abs(a["gap"]), reverse=True)
        return anomalies

    def _absence_insight(self):
        with_absence = [s["average"] for s in self.students if (s.get("absence") or 0) > 0]
        without_absence = [s["average"] for s in self.students if (s.get("absence") or 0) == 0]
        if with_absence and without_absence and len(with_absence) >= 3:
            diff = statistics.mean(without_absence) - statistics.mean(with_absence)
            if diff > 3:
                return f"الطلاب الذين لديهم غياب حقّقوا معدلاً أقل بمقدار {round(diff,1)} نقطة تقريبًا"
        return None

    def student_table_rows(self):
        rows = []
        for s in sorted(self.students, key=lambda s: s["average"], reverse=True):
            rows.append({
                "الاسم": s["name_ar"],
                "الفصل": s.get("class"),
                "المعدل": s["average"],
                "التقدير": s.get("general_grade"),
                "ترتيب الصف": s.get("rank_in_grade"),
                "ترتيب الفصل": s.get("rank_in_class"),
                "الغياب": s.get("absence"),
            })
        return rows

    def find_student(self, name_ar, class_value=None):
        """يبحث عن طالب بالاسم (ومطابقة الفصل اختياريًا لتفادي تشابه الأسماء)."""
        candidates = [s for s in self.students if s["name_ar"] == name_ar]
        if class_value is not None:
            narrowed = [s for s in candidates if str(s.get("class")) == str(class_value)]
            if narrowed:
                return narrowed[0]
        return candidates[0] if candidates else None

    def available_subjects(self):
        """يرجع قائمة كل المواد الأكاديمية الموجودة بالملف (بدون المواظبة/السلوك/النشاط)."""
        names = set()
        for s in self.students:
            for sub in s.get("subjects", []):
                if sub.get("total_pct") is not None and sub["subject_ar"] not in NON_ACADEMIC_SUBJECTS:
                    names.add(sub["subject_ar"])
        return sorted(names)

    def subject_report(self, subject_name, weakest_n=5):
        """
        يبني تحليلًا مخصصًا لمادة واحدة: متوسط عام، متوسط كل فصل لهذي المادة فقط،
        توزيع التقديرات بهذي المادة، وأضعف N طلاب بها تحديدًا.
        """
        rows = []
        for s in self.students:
            for sub in s.get("subjects", []):
                if sub["subject_ar"] == subject_name and sub.get("total_pct") is not None:
                    rows.append({
                        "student": s,
                        "pct": sub["total_pct"],
                        "grade_label": sub.get("grade_label"),
                    })

        if not rows:
            return None

        pct_values = [r["pct"] for r in rows]
        overall_avg = round(statistics.mean(pct_values), 2)

        class_groups = defaultdict(list)
        for r in rows:
            cls = r["student"].get("class") or "غير محدد"
            class_groups[cls].append(r["pct"])
        class_stats = {
            cls: {"mean": round(statistics.mean(vals), 2), "count": len(vals),
                  "min": round(min(vals), 2), "max": round(max(vals), 2)}
            for cls, vals in class_groups.items()
        }

        grade_counts = defaultdict(int)
        for r in rows:
            g = r["grade_label"] or "غير محدد"
            grade_counts[g] += 1

        weakest = sorted(rows, key=lambda r: r["pct"])[:weakest_n]
        strongest = sorted(rows, key=lambda r: r["pct"], reverse=True)[:weakest_n]

        return {
            "subject_name": subject_name,
            "count": len(rows),
            "overall_avg": overall_avg,
            "highest": max(pct_values),
            "lowest": min(pct_values),
            "class_stats": class_stats,
            "grade_distribution": dict(grade_counts),
            "weakest": weakest,
            "strongest": strongest,
            "all_rows": sorted(rows, key=lambda r: r["pct"], reverse=True),
        }

    def student_insight(self, student):
        """
        يبني ملاحظات تلقائية عن طالب معيّن: أقوى وأضعف مادة، مقارنة بمتوسط
        الفصل، وحالة الغياب. يُستخدم في تقرير الطالب الفردي.
        """
        subjects = [s for s in student.get("subjects", [])
                    if s.get("total_pct") is not None and s["subject_ar"] not in NON_ACADEMIC_SUBJECTS]
        notes = []

        if subjects:
            best = max(subjects, key=lambda s: s["total_pct"])
            worst = min(subjects, key=lambda s: s["total_pct"])
            if best["subject_ar"] != worst["subject_ar"]:
                notes.append(f"أقوى أداء في مادة {best['subject_ar']} بنسبة {best['total_pct']}%")
                if worst["total_pct"] < 75:
                    notes.append(f"يحتاج تعزيز في مادة {worst['subject_ar']} بنسبة {worst['total_pct']}%")

        cls = student.get("class")
        class_mean = self.class_stats.get(cls, {}).get("mean") if cls in self.class_stats else None
        if class_mean is not None and student.get("average") is not None:
            diff = round(student["average"] - class_mean, 1)
            if diff > 2:
                notes.append(f"معدله أعلى من متوسط فصله بمقدار {diff} نقطة")
            elif diff < -2:
                notes.append(f"معدله أقل من متوسط فصله بمقدار {abs(diff)} نقطة")
            else:
                notes.append("معدله قريب من متوسط فصله")

        absence = student.get("absence") or 0
        if absence and absence > 0:
            notes.append(f"لديه {absence} يوم غياب بدون عذر")

        if student.get("average") is not None and student["average"] < self.risk_threshold:
            notes.append("يحتاج متابعة عاجلة لتحسين مستواه")

        return notes
