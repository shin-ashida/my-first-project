"""
物流現場 高度財務分析ツール

機能:
1. 基本収益性分析（前年比較・月次推移）
2. 課題抽出（閾値ベース）
3. 経営KPI整合性チェック
4. [拡張] コスト構造の異常検知・要因分解
5. [拡張] 売上と原価の連動性・損益分岐点分析
6. [拡張] 生産性劣化パターン・相関分析
7. [拡張] 多角的比較（移動平均・前月比・ベスト/ワースト）
8. [拡張] データ異常値の自動検出
"""

import csv
import os
import math
from dataclasses import dataclass


# ============================================================
# データ構造
# ============================================================

@dataclass
class MonthlyRecord:
    """現場の月次PLデータ"""
    site_name: str
    year: int
    month: int
    revenue: int
    shipments: int
    touch_count: int
    avg_unit_price: float
    admin_cost: int
    other_revenue: int
    salary_cost: int
    employee_total_hours: float
    employee_regular_hours: float
    employee_overtime_hours: float
    employee_count: float
    labor_cost: int
    staff_hours: float
    avg_hourly_wage: int
    outsource_cost: int
    timee_hours: float
    timee_hourly_cost: int
    paid_leave: int
    statutory_welfare: int
    travel_expense: int

    @property
    def period_label(self) -> str:
        return f"{self.year}年{self.month}月"

    @property
    def total_cost(self) -> int:
        return (self.salary_cost + self.labor_cost + self.outsource_cost
                + self.paid_leave + self.statutory_welfare + self.travel_expense)

    @property
    def gross_profit(self) -> int:
        return self.revenue - self.total_cost

    @property
    def gross_margin(self) -> float:
        return (self.gross_profit / self.revenue * 100) if self.revenue else 0.0

    @property
    def cost_ratio(self) -> float:
        return (self.total_cost / self.revenue * 100) if self.revenue else 0.0

    @property
    def labor_cost_ratio(self) -> float:
        return (self.labor_cost / self.revenue * 100) if self.revenue else 0.0

    @property
    def total_hours(self) -> float:
        return self.employee_total_hours + self.staff_hours + self.timee_hours

    @property
    def productivity(self) -> float:
        return (self.touch_count / self.total_hours) if self.total_hours else 0.0

    @property
    def revenue_per_employee(self) -> float:
        return (self.revenue / self.employee_count) if self.employee_count else 0.0

    @property
    def overtime_ratio(self) -> float:
        return (self.employee_overtime_hours / self.employee_total_hours * 100) if self.employee_total_hours else 0.0

    def cost_items(self) -> dict[str, int]:
        """コスト項目の辞書を返す"""
        return {
            "給与手当": self.salary_cost,
            "労務費": self.labor_cost,
            "外注費": self.outsource_cost,
            "有給": self.paid_leave,
            "法定福利費": self.statutory_welfare,
            "旅費交通費": self.travel_expense,
        }


# ============================================================
# データ読み込み
# ============================================================

def load_data(filepath: str) -> list[MonthlyRecord]:
    records = []
    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(MonthlyRecord(
                site_name=row["site_name"],
                year=int(row["year"]),
                month=int(row["month"]),
                revenue=int(row["revenue"]),
                shipments=int(row["shipments"]),
                touch_count=int(row["touch_count"]),
                avg_unit_price=float(row["avg_unit_price"]),
                admin_cost=int(row["admin_cost"]),
                other_revenue=int(row["other_revenue"]),
                salary_cost=int(row["salary_cost"]),
                employee_total_hours=float(row["employee_total_hours"]),
                employee_regular_hours=float(row["employee_regular_hours"]),
                employee_overtime_hours=float(row["employee_overtime_hours"]),
                employee_count=float(row["employee_count"]),
                labor_cost=int(row["labor_cost"]),
                staff_hours=float(row["staff_hours"]),
                avg_hourly_wage=int(row["avg_hourly_wage"]),
                outsource_cost=int(row["outsource_cost"]),
                timee_hours=float(row["timee_hours"]),
                timee_hourly_cost=int(row["timee_hourly_cost"]),
                paid_leave=int(row["paid_leave"]),
                statutory_welfare=int(row["statutory_welfare"]),
                travel_expense=int(row["travel_expense"]),
            ))
    return records


# ============================================================
# ユーティリティ
# ============================================================

def fmt(amount: int) -> str:
    return f"¥{amount:,}"

def fmt_man(amount: int) -> str:
    return f"{amount / 10000:,.0f}万円"

def pct(value: float) -> str:
    return f"{value:.1f}%"

def sep(char: str = "=", width: int = 80):
    print(char * width)

def group_by_site(records: list[MonthlyRecord]) -> dict[str, list[MonthlyRecord]]:
    sites: dict[str, list[MonthlyRecord]] = {}
    for r in records:
        sites.setdefault(r.site_name, []).append(r)
    return sites

def find_pair(recs: list[MonthlyRecord], year: int, month: int):
    for r in recs:
        if r.year == year and r.month == month:
            return r
    return None

def sort_by_time(recs: list[MonthlyRecord]) -> list[MonthlyRecord]:
    return sorted(recs, key=lambda r: (r.year, r.month))

def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0

def stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))

def moving_average(values: list[float], window: int = 3) -> list[float | None]:
    result = []
    for i in range(len(values)):
        if i < window - 1:
            result.append(None)
        else:
            result.append(mean(values[i - window + 1:i + 1]))
    return result

def correlation(xs: list[float], ys: list[float]) -> float:
    """ピアソン相関係数"""
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return 0.0
    return num / (dx * dy)


# ============================================================
# 1. 基本収益性分析（既存）
# ============================================================

def analyze_profitability(records: list[MonthlyRecord]) -> None:
    print()
    sep()
    print("  1. 現場別 収益性分析")
    sep()

    sites = group_by_site(records)
    for site_name, recs in sites.items():
        print(f"\n{'─' * 80}")
        print(f"  現場: {site_name}")
        print(f"{'─' * 80}")

        years = sorted(set(r.year for r in recs))
        for year in years:
            yr = [r for r in recs if r.year == year]
            rev = sum(r.revenue for r in yr)
            cost = sum(r.total_cost for r in yr)
            profit = sum(r.gross_profit for r in yr)
            margin = (profit / rev * 100) if rev else 0
            print(f"\n  【{year}年 合計】売上: {fmt(rev)} / 原価: {fmt(cost)} / 粗利: {fmt(profit)} / 粗利率: {pct(margin)}")

        months = sorted(set(r.month for r in recs))
        max_year, min_year = max(years), min(years)

        print(f"\n  【月次推移】{min_year}年 vs {max_year}年")
        print(f"  {'月':>4s}  {'売上(前年)':>14s}  {'売上(今年)':>14s}  {'前年比':>8s}  {'粗利率(前年)':>10s}  {'粗利率(今年)':>10s}  {'生産性(前年)':>10s}  {'生産性(今年)':>10s}")
        print(f"  {'─' * 76}")

        for m in months:
            prev = find_pair(recs, min_year, m)
            curr = find_pair(recs, max_year, m)
            prev_rev = fmt(prev.revenue) if prev else "-"
            curr_rev = fmt(curr.revenue) if curr else "-"
            yoy = ""
            if prev and curr and prev.revenue > 0:
                yoy = f"{(curr.revenue - prev.revenue) / prev.revenue * 100:+.1f}%"
            prev_m = pct(prev.gross_margin) if prev else "-"
            curr_m = pct(curr.gross_margin) if curr else "-"
            prev_p = f"{prev.productivity:.1f}" if prev else "-"
            curr_p = f"{curr.productivity:.1f}" if curr else "-"
            print(f"  {m:>3d}月  {prev_rev:>14s}  {curr_rev:>14s}  {yoy:>8s}  {prev_m:>10s}  {curr_m:>10s}  {prev_p:>10s}  {curr_p:>10s}")


# ============================================================
# 2. 課題抽出（既存）
# ============================================================

THRESHOLDS = {
    "low_gross_margin": 20.0,
    "high_cost_ratio": 80.0,
    "high_labor_ratio": 55.0,
    "low_productivity": 70,
    "productivity_decline": -10.0,
    "high_overtime_ratio": 15.0,
    "revenue_decline": -5.0,
    "margin_decline": -5.0,
}

def extract_issues(records: list[MonthlyRecord]) -> None:
    print()
    sep()
    print("  2. 現場ごとの課題抽出")
    sep()

    sites = group_by_site(records)
    years = sorted(set(r.year for r in records))
    max_year, min_year = max(years), min(years)

    for site_name, recs in sites.items():
        issues = []
        months = sorted(set(r.month for r in recs))

        for m in months:
            curr = find_pair(recs, max_year, m)
            prev = find_pair(recs, min_year, m)
            if not curr:
                continue
            label = f"{max_year}年{m}月"

            if curr.gross_margin < THRESHOLDS["low_gross_margin"]:
                sev = "HIGH" if curr.gross_margin < 15 else "MEDIUM"
                issues.append((sev, "収益性", label, f"粗利率 {pct(curr.gross_margin)} (基準: {pct(THRESHOLDS['low_gross_margin'])}以上)"))

            if curr.cost_ratio > THRESHOLDS["high_cost_ratio"]:
                sev = "HIGH" if curr.cost_ratio > 85 else "MEDIUM"
                issues.append((sev, "コスト", label, f"原価率 {pct(curr.cost_ratio)} (基準: {pct(THRESHOLDS['high_cost_ratio'])}以下)"))

            if curr.labor_cost_ratio > THRESHOLDS["high_labor_ratio"]:
                sev = "HIGH" if curr.labor_cost_ratio > 60 else "MEDIUM"
                issues.append((sev, "人件費", label, f"労務費/売上 {pct(curr.labor_cost_ratio)} (基準: {pct(THRESHOLDS['high_labor_ratio'])}以下)"))

            if curr.productivity < THRESHOLDS["low_productivity"]:
                sev = "HIGH" if curr.productivity < 60 else "MEDIUM"
                issues.append((sev, "生産性", label, f"生産性 {curr.productivity:.1f} (基準: {THRESHOLDS['low_productivity']}以上)"))

            if prev and prev.productivity > 0:
                pc = ((curr.productivity - prev.productivity) / prev.productivity) * 100
                if pc < THRESHOLDS["productivity_decline"]:
                    sev = "HIGH" if pc < -20 else "MEDIUM"
                    issues.append((sev, "生産性", label, f"生産性前年比 {pc:+.1f}% (基準: {THRESHOLDS['productivity_decline']}%以上)"))

            if curr.overtime_ratio > THRESHOLDS["high_overtime_ratio"]:
                sev = "HIGH" if curr.overtime_ratio > 20 else "MEDIUM"
                issues.append((sev, "労務", label, f"残業率 {pct(curr.overtime_ratio)} (基準: {pct(THRESHOLDS['high_overtime_ratio'])}以下)"))

            if prev and prev.revenue > 0:
                rc = (curr.revenue - prev.revenue) / prev.revenue * 100
                if rc < THRESHOLDS["revenue_decline"]:
                    issues.append(("MEDIUM", "売上", label, f"売上前年比 {rc:+.1f}% (基準: {THRESHOLDS['revenue_decline']}%以上)"))

            if prev:
                md = curr.gross_margin - prev.gross_margin
                if md < THRESHOLDS["margin_decline"]:
                    sev = "HIGH" if md < -10 else "MEDIUM"
                    issues.append((sev, "収益性", label, f"粗利率前年差 {md:+.1f}pt (前年{pct(prev.gross_margin)}→今年{pct(curr.gross_margin)})"))

        high_c = sum(1 for i in issues if i[0] == "HIGH")
        med_c = sum(1 for i in issues if i[0] == "MEDIUM")
        status = "要改善" if high_c > 0 else ("要注意" if med_c > 0 else "良好")

        print(f"\n  [{status}] {site_name} - HIGH: {high_c}件 / MEDIUM: {med_c}件")
        print(f"  {'─' * 70}")
        for sev, cat, period, desc in issues:
            mark = "!!" if sev == "HIGH" else "! "
            print(f"    {mark} [{cat}] {period}: {desc}")

        if issues:
            cats = {}
            for sev, cat, _, _ in issues:
                cats.setdefault(cat, {"HIGH": 0, "MEDIUM": 0})
                cats[cat][sev] += 1
            print(f"\n    課題サマリ:")
            for cat, c in sorted(cats.items(), key=lambda x: x[1]["HIGH"], reverse=True):
                print(f"      {cat}: HIGH {c['HIGH']}件, MEDIUM {c['MEDIUM']}件")


# ============================================================
# 3. 経営KPI整合性チェック（既存）
# ============================================================

MANAGEMENT_KPIS = {
    "粗利率": {"target": 25.0, "unit": "%", "direction": "higher"},
    "原価率": {"target": 75.0, "unit": "%", "direction": "lower"},
    "労務費比率": {"target": 50.0, "unit": "%", "direction": "lower"},
    "生産性(タッチ/時間)": {"target": 80, "unit": "", "direction": "higher"},
    "社員一人あたり売上": {"target": 4000000, "unit": "円", "direction": "higher"},
    "残業率": {"target": 10.0, "unit": "%", "direction": "lower"},
    "売上前年成長率": {"target": 5.0, "unit": "%", "direction": "higher"},
}

def check_kpi_alignment(records: list[MonthlyRecord]) -> None:
    print()
    sep()
    print("  3. 経営KPI と 現場KPI の整合性チェック")
    sep()

    sites = group_by_site(records)
    years = sorted(set(r.year for r in records))
    max_year, min_year = max(years), min(years)

    for site_name, recs in sites.items():
        print(f"\n{'─' * 80}")
        print(f"  現場: {site_name}")
        print(f"{'─' * 80}")

        curr_recs = [r for r in recs if r.year == max_year]
        prev_recs = [r for r in recs if r.year == min_year]
        if not curr_recs:
            continue

        curr_rev = sum(r.revenue for r in curr_recs)
        curr_cost = sum(r.total_cost for r in curr_recs)
        curr_labor = sum(r.labor_cost for r in curr_recs)
        curr_touch = sum(r.touch_count for r in curr_recs)
        curr_hours = sum(r.total_hours for r in curr_recs)
        curr_emp = sum(r.employee_count for r in curr_recs) / len(curr_recs)
        curr_ot = sum(r.employee_overtime_hours for r in curr_recs)
        curr_eh = sum(r.employee_total_hours for r in curr_recs)
        prev_rev = sum(r.revenue for r in prev_recs) if prev_recs else 0

        actuals = {
            "粗利率": ((curr_rev - curr_cost) / curr_rev * 100) if curr_rev else 0,
            "原価率": (curr_cost / curr_rev * 100) if curr_rev else 0,
            "労務費比率": (curr_labor / curr_rev * 100) if curr_rev else 0,
            "生産性(タッチ/時間)": (curr_touch / curr_hours) if curr_hours else 0,
            "社員一人あたり売上": (curr_rev / curr_emp) if curr_emp else 0,
            "残業率": (curr_ot / curr_eh * 100) if curr_eh else 0,
            "売上前年成長率": ((curr_rev - prev_rev) / prev_rev * 100) if prev_rev else 0,
        }

        ok_count = 0
        ng_count = 0
        print(f"\n  {'KPI名':<22s}  {'目標':>12s}  {'実績':>12s}  {'判定':>4s}  {'乖離':>10s}")
        print(f"  {'─' * 68}")

        for kpi_name, info in MANAGEMENT_KPIS.items():
            target, unit, direction = info["target"], info["unit"], info["direction"]
            actual = actuals.get(kpi_name, 0)
            if direction == "higher":
                met = actual >= target
                gap = actual - target
            else:
                met = actual <= target
                gap = target - actual
            mark = "OK" if met else "NG"
            ok_count += met
            ng_count += (not met)

            if kpi_name == "社員一人あたり売上":
                print(f"  {kpi_name:<20s}  {fmt(int(target)):>12s}  {fmt(int(actual)):>12s}  [{mark}]  {fmt(int(gap)):>10s}")
            else:
                print(f"  {kpi_name:<20s}  {target:.1f}{unit:>10s}  {actual:.1f}{unit:>10s}  [{mark}]  {gap:+.1f}{unit:>8s}")

        total = ok_count + ng_count
        rate = (ok_count / total * 100) if total else 0
        bar = "■" * int(rate / 5) + "□" * (20 - int(rate / 5))
        print(f"\n  KPI達成率: {ok_count}/{total} ({rate:.0f}%) [{bar}]")


# ============================================================
# 4. [拡張] コスト構造の異常検知・要因分解
# ============================================================

def analyze_cost_structure(records: list[MonthlyRecord]) -> None:
    print()
    sep()
    print("  4. コスト構造の異常検知・要因分解")
    sep()

    sites = group_by_site(records)
    years = sorted(set(r.year for r in records))
    max_year, min_year = max(years), min(years)

    for site_name, recs in sites.items():
        print(f"\n{'─' * 80}")
        print(f"  現場: {site_name}")
        print(f"{'─' * 80}")

        # --- 4a. コスト項目ごとの前年比変化と寄与度分析 ---
        print(f"\n  【粗利率悪化の要因分解】{min_year}年 → {max_year}年")
        prev_recs = sorted([r for r in recs if r.year == min_year], key=lambda r: r.month)
        curr_recs = sorted([r for r in recs if r.year == max_year], key=lambda r: r.month)

        prev_rev = sum(r.revenue for r in prev_recs)
        curr_rev = sum(r.revenue for r in curr_recs)
        prev_cost = sum(r.total_cost for r in prev_recs)
        curr_cost = sum(r.total_cost for r in curr_recs)

        rev_growth = ((curr_rev - prev_rev) / prev_rev * 100) if prev_rev else 0
        cost_growth = ((curr_cost - prev_cost) / prev_cost * 100) if prev_cost else 0

        print(f"\n    売上成長率: {rev_growth:+.1f}%")
        print(f"    原価成長率: {cost_growth:+.1f}%")
        if cost_growth > rev_growth:
            print(f"    >>> 原価の伸び({cost_growth:+.1f}%)が売上の伸び({rev_growth:+.1f}%)を上回っている！")

        # コスト項目別寄与度
        cost_labels = ["給与手当", "労務費", "外注費", "有給", "法定福利費", "旅費交通費"]
        prev_items = {k: 0 for k in cost_labels}
        curr_items = {k: 0 for k in cost_labels}
        for r in prev_recs:
            for k, v in r.cost_items().items():
                prev_items[k] += v
        for r in curr_recs:
            for k, v in r.cost_items().items():
                curr_items[k] += v

        total_cost_increase = curr_cost - prev_cost
        print(f"\n    原価増加額: {fmt(total_cost_increase)} の内訳:")
        print(f"    {'項目':<12s}  {'前年':>12s}  {'今年':>12s}  {'増減':>12s}  {'寄与度':>8s}  {'増減率':>8s}")
        print(f"    {'─' * 64}")

        contributions = []
        for label in cost_labels:
            prev_v = prev_items[label]
            curr_v = curr_items[label]
            diff = curr_v - prev_v
            contrib = (diff / total_cost_increase * 100) if total_cost_increase else 0
            growth = ((diff / prev_v) * 100) if prev_v else (100.0 if curr_v > 0 else 0.0)
            contributions.append((label, prev_v, curr_v, diff, contrib, growth))

        for label, pv, cv, diff, contrib, growth in sorted(contributions, key=lambda x: abs(x[4]), reverse=True):
            mark = " <<<" if abs(contrib) > 30 else ""
            print(f"    {label:<10s}  {fmt_man(pv):>12s}  {fmt_man(cv):>12s}  {fmt_man(diff):>12s}  {contrib:>+7.1f}%  {growth:>+7.1f}%{mark}")

        # --- 4b. 月次コスト比率の急変検出 ---
        print(f"\n  【月次コスト比率の急変検出】")

        all_sorted = sort_by_time(recs)
        anomalies = []

        for i in range(1, len(all_sorted)):
            curr = all_sorted[i]
            prev = all_sorted[i - 1]
            if curr.revenue == 0 or prev.revenue == 0:
                continue

            for label in cost_labels:
                curr_v = curr.cost_items()[label]
                prev_v = prev.cost_items()[label]
                curr_ratio = curr_v / curr.revenue * 100
                prev_ratio = prev_v / prev.revenue * 100
                diff = curr_ratio - prev_ratio

                # 比率が5pt以上急変、または金額がゼロから発生
                if abs(diff) > 5.0 or (prev_v == 0 and curr_v > 100000):
                    anomalies.append({
                        "period": curr.period_label,
                        "item": label,
                        "prev_ratio": prev_ratio,
                        "curr_ratio": curr_ratio,
                        "diff": diff,
                        "prev_amount": prev_v,
                        "curr_amount": curr_v,
                    })

        if anomalies:
            for a in anomalies:
                direction = "急増" if a["diff"] > 0 else "急減"
                print(f"    {a['period']}: {a['item']} {direction} (対売上比 {a['prev_ratio']:.1f}%→{a['curr_ratio']:.1f}%, {a['diff']:+.1f}pt, 金額 {fmt_man(a['prev_amount'])}→{fmt_man(a['curr_amount'])})")
        else:
            print("    急変なし")

        # --- 4c. 労務費の要因分解（時給 × 工数） ---
        print(f"\n  【労務費の要因分解: 時給 × 工数】")
        months = sorted(set(r.month for r in recs))
        print(f"    {'月':>6s}  {'時給(前年)':>10s}  {'時給(今年)':>10s}  {'工数(前年)':>10s}  {'工数(今年)':>10s}  {'主因':>10s}")
        print(f"    {'─' * 60}")

        for m in months:
            prev = find_pair(recs, min_year, m)
            curr = find_pair(recs, max_year, m)
            if not prev or not curr:
                continue

            wage_change = curr.avg_hourly_wage - prev.avg_hourly_wage
            hours_change = curr.staff_hours - prev.staff_hours

            # 寄与度分解: ΔCost ≈ ΔWage×PrevHours + PrevWage×ΔHours
            wage_effect = wage_change * prev.staff_hours
            hours_effect = prev.avg_hourly_wage * hours_change

            if abs(wage_effect) > abs(hours_effect):
                cause = "時給↑" if wage_change > 0 else "時給↓"
            else:
                cause = "工数↑" if hours_change > 0 else "工数↓"

            print(f"    {m:>4d}月  ¥{prev.avg_hourly_wage:>8,d}  ¥{curr.avg_hourly_wage:>8,d}  {prev.staff_hours:>9.0f}h  {curr.staff_hours:>9.0f}h  {cause:>10s}")


# ============================================================
# 5. [拡張] 売上と原価の連動性・損益分岐点分析
# ============================================================

def analyze_revenue_cost_linkage(records: list[MonthlyRecord]) -> None:
    print()
    sep()
    print("  5. 売上と原価の連動性・損益分岐点分析")
    sep()

    sites = group_by_site(records)

    for site_name, recs in sites.items():
        print(f"\n{'─' * 80}")
        print(f"  現場: {site_name}")
        print(f"{'─' * 80}")

        sorted_recs = sort_by_time(recs)
        revenues = [r.revenue for r in sorted_recs]
        costs = [r.total_cost for r in sorted_recs]

        # --- 5a. 変動費率の推定（単回帰: cost = a * revenue + b） ---
        n = len(revenues)
        if n < 3:
            print("    データが不足しています。")
            continue

        # 最小二乗法
        sum_x = sum(revenues)
        sum_y = sum(costs)
        sum_xy = sum(x * y for x, y in zip(revenues, costs))
        sum_x2 = sum(x * x for x in revenues)

        denom = n * sum_x2 - sum_x ** 2
        if denom == 0:
            print("    回帰計算ができません。")
            continue

        a = (n * sum_xy - sum_x * sum_y) / denom  # 変動費率
        b = (sum_y - a * sum_x) / n                # 固定費

        print(f"\n  【コスト構造モデル（回帰分析）】")
        print(f"    原価 = {a:.3f} × 売上 + {fmt(int(b))}")
        print(f"    推定変動費率: {pct(a * 100)}")
        print(f"    推定月間固定費: {fmt_man(int(b))}")

        # 損益分岐点: revenue = fixed_cost / (1 - variable_rate)
        if a < 1.0:
            bep = b / (1 - a)
            print(f"    損益分岐点売上: {fmt_man(int(bep))}/月")
            # 現在の平均売上との比較
            avg_rev = mean(revenues)
            safety_margin = (avg_rev - bep) / avg_rev * 100
            print(f"    平均月間売上: {fmt_man(int(avg_rev))}")
            print(f"    安全余裕率: {pct(safety_margin)} {'(余裕あり)' if safety_margin > 20 else '(要注意)' if safety_margin > 0 else '(危険!)'}")
        else:
            print(f"    >>> 変動費率が100%超 - 売上が増えるほど赤字が拡大する構造！")

        # --- 5b. 売上増 vs 原価増の乖離パターン ---
        print(f"\n  【売上増減と原価増減の乖離（前月比）】")
        print(f"    {'期間':>12s}  {'売上変動':>10s}  {'原価変動':>10s}  {'乖離':>8s}  {'判定':>8s}")
        print(f"    {'─' * 54}")

        for i in range(1, len(sorted_recs)):
            curr, prev = sorted_recs[i], sorted_recs[i - 1]
            if prev.revenue == 0:
                continue
            rev_chg = (curr.revenue - prev.revenue) / prev.revenue * 100
            cost_chg = (curr.total_cost - prev.total_cost) / prev.total_cost * 100 if prev.total_cost else 0
            gap = cost_chg - rev_chg

            # 原価の伸びが売上の伸びを10pt以上上回る場合に警告
            if gap > 10:
                flag = "!! 原価過大"
            elif gap > 5:
                flag = "!  要注意"
            elif rev_chg > 5 and cost_chg < rev_chg:
                flag = "良好"
            else:
                flag = ""

            if flag:
                print(f"    {curr.period_label:>10s}  {rev_chg:>+9.1f}%  {cost_chg:>+9.1f}%  {gap:>+7.1f}pt  {flag}")

        # --- 5c. 相関係数 ---
        r_val = correlation(revenues, costs)
        print(f"\n    売上-原価の相関係数: {r_val:.3f}", end="")
        if r_val > 0.9:
            print(" (非常に強い正の相関 → 変動費主体)")
        elif r_val > 0.7:
            print(" (強い正の相関)")
        elif r_val > 0.5:
            print(" (中程度の相関 → 固定費の影響あり)")
        else:
            print(" (弱い相関 → コスト管理に問題の可能性)")


# ============================================================
# 6. [拡張] 生産性劣化パターン・相関分析
# ============================================================

def analyze_productivity_patterns(records: list[MonthlyRecord]) -> None:
    print()
    sep()
    print("  6. 生産性劣化パターン・相関分析")
    sep()

    sites = group_by_site(records)
    years = sorted(set(r.year for r in records))
    max_year = max(years)

    for site_name, recs in sites.items():
        print(f"\n{'─' * 80}")
        print(f"  現場: {site_name}")
        print(f"{'─' * 80}")

        curr_recs = sorted([r for r in recs if r.year == max_year], key=lambda r: r.month)
        all_sorted = sort_by_time(recs)

        # --- 6a. トレンド分析 ---
        print(f"\n  【生産性トレンド分析 ({max_year}年)】")
        prods = [r.productivity for r in curr_recs]
        months_list = [r.month for r in curr_recs]
        ma = moving_average(prods, 3)

        # 線形トレンド（簡易版）
        if len(prods) >= 3:
            xs = list(range(len(prods)))
            n = len(xs)
            sx = sum(xs)
            sy = sum(prods)
            sxy = sum(x * y for x, y in zip(xs, prods))
            sx2 = sum(x * x for x in xs)
            denom = n * sx2 - sx ** 2
            if denom != 0:
                slope = (n * sxy - sx * sy) / denom
                trend_dir = "下降トレンド ↓" if slope < -2 else ("上昇トレンド ↑" if slope > 2 else "横ばい →")
                print(f"    トレンド: {trend_dir} (月あたり {slope:+.1f}pt)")
            else:
                slope = 0

        print(f"\n    {'月':>4s}  {'生産性':>8s}  {'3ヶ月移動平均':>12s}  {'トレンドからの乖離':>16s}")
        print(f"    {'─' * 46}")

        for i, r in enumerate(curr_recs):
            ma_val = f"{ma[i]:.1f}" if ma[i] is not None else "-"
            # トレンドからの乖離
            expected = (slope * i + (sy / n - slope * sx / n)) if denom != 0 else prods[i]
            deviation = prods[i] - expected
            flag = " !! 異常" if abs(deviation) > 15 else ""
            print(f"    {r.month:>3d}月  {prods[i]:>7.1f}  {ma_val:>12s}  {deviation:>+15.1f}{flag}")

        # --- 6b. 工数バランス変化 ---
        print(f"\n  【工数バランス変化 ({max_year}年)】")
        print(f"    {'月':>4s}  {'社員工数':>8s}  {'スタッフ':>8s}  {'タイミー':>8s}  {'社員比率':>8s}  {'外部依存度':>10s}")
        print(f"    {'─' * 52}")

        for r in curr_recs:
            total = r.total_hours
            if total == 0:
                continue
            emp_pct = r.employee_total_hours / total * 100
            staff_pct = r.staff_hours / total * 100
            timee_pct = r.timee_hours / total * 100
            external = staff_pct + timee_pct

            flag = " !! 外部依存過多" if external > 95 else (" ! 外部依存高" if external > 90 else "")
            print(f"    {r.month:>3d}月  {r.employee_total_hours:>7.0f}h  {r.staff_hours:>7.0f}h  {r.timee_hours:>7.0f}h  {pct(emp_pct):>8s}  {pct(external):>10s}{flag}")

        # --- 6c. 相関分析 ---
        print(f"\n  【相関分析（全期間）】")

        all_prods = [r.productivity for r in all_sorted if r.total_hours > 0]
        all_ot = [r.overtime_ratio for r in all_sorted if r.total_hours > 0]
        all_margins = [r.gross_margin for r in all_sorted if r.total_hours > 0]
        all_staff_ratio = [(r.staff_hours / r.total_hours * 100) if r.total_hours > 0 else 0 for r in all_sorted if r.total_hours > 0]
        all_emp_hours = [r.employee_total_hours for r in all_sorted if r.total_hours > 0]

        correlations = [
            ("残業率 vs 生産性", correlation(all_ot, all_prods)),
            ("生産性 vs 粗利率", correlation(all_prods, all_margins)),
            ("スタッフ比率 vs 生産性", correlation(all_staff_ratio, all_prods)),
            ("社員工数 vs 生産性", correlation(all_emp_hours, all_prods)),
        ]

        for label, r_val in correlations:
            strength = ""
            if abs(r_val) > 0.7:
                strength = "★強い相関"
            elif abs(r_val) > 0.4:
                strength = "中程度"
            else:
                strength = "弱い"
            direction = "正" if r_val > 0 else "負"
            print(f"    {label:<24s}: {r_val:>+.3f} ({direction}の{strength})")

        # 解釈
        ot_prod_corr = correlation(all_ot, all_prods)
        if ot_prod_corr < -0.4:
            print(f"\n    >>> 残業が増えると生産性が下がる傾向が見られます。")
            print(f"        残業削減が生産性改善につながる可能性があります。")


# ============================================================
# 7. [拡張] 多角的比較（移動平均・前月比・ベスト/ワースト）
# ============================================================

def analyze_multi_angle(records: list[MonthlyRecord]) -> None:
    print()
    sep()
    print("  7. 多角的比較分析")
    sep()

    sites = group_by_site(records)
    years = sorted(set(r.year for r in records))
    max_year = max(years)

    for site_name, recs in sites.items():
        print(f"\n{'─' * 80}")
        print(f"  現場: {site_name}")
        print(f"{'─' * 80}")

        curr_recs = sorted([r for r in recs if r.year == max_year], key=lambda r: r.month)

        # --- 7a. 前月比変化 ---
        print(f"\n  【前月比変化 ({max_year}年)】")
        print(f"    {'月':>4s}  {'売上前月比':>10s}  {'原価前月比':>10s}  {'粗利率変動':>10s}  {'生産性変動':>10s}  {'急変アラート':>12s}")
        print(f"    {'─' * 62}")

        for i in range(1, len(curr_recs)):
            curr, prev = curr_recs[i], curr_recs[i - 1]
            rev_chg = ((curr.revenue - prev.revenue) / prev.revenue * 100) if prev.revenue else 0
            cost_chg = ((curr.total_cost - prev.total_cost) / prev.total_cost * 100) if prev.total_cost else 0
            margin_chg = curr.gross_margin - prev.gross_margin
            prod_chg = curr.productivity - prev.productivity if prev.total_hours > 0 else 0

            alerts = []
            if abs(rev_chg) > 15:
                alerts.append("売上急変")
            if abs(margin_chg) > 5:
                alerts.append("利益率急変")
            if abs(prod_chg) > 15:
                alerts.append("生産性急変")

            alert_str = ", ".join(alerts) if alerts else ""
            print(f"    {curr.month:>3d}月  {rev_chg:>+9.1f}%  {cost_chg:>+9.1f}%  {margin_chg:>+9.1f}pt  {prod_chg:>+9.1f}  {alert_str}")

        # --- 7b. 3ヶ月移動平均（季節変動除去） ---
        print(f"\n  【3ヶ月移動平均（季節変動除去）】")
        margins = [r.gross_margin for r in curr_recs]
        prods = [r.productivity for r in curr_recs]
        ma_margins = moving_average(margins, 3)
        ma_prods = moving_average(prods, 3)

        print(f"    {'月':>4s}  {'粗利率':>8s}  {'移動平均':>8s}  {'方向':>6s}  {'生産性':>8s}  {'移動平均':>8s}  {'方向':>6s}")
        print(f"    {'─' * 52}")

        for i, r in enumerate(curr_recs):
            m_ma = f"{ma_margins[i]:.1f}%" if ma_margins[i] is not None else "-"
            p_ma = f"{ma_prods[i]:.1f}" if ma_prods[i] is not None else "-"

            m_dir = ""
            p_dir = ""
            if i >= 2 and ma_margins[i] is not None and ma_margins[i - 1] is not None:
                m_dir = "↑" if ma_margins[i] > ma_margins[i - 1] else "↓"
            if i >= 2 and ma_prods[i] is not None and ma_prods[i - 1] is not None:
                p_dir = "↑" if ma_prods[i] > ma_prods[i - 1] else "↓"

            print(f"    {r.month:>3d}月  {pct(margins[i]):>8s}  {m_ma:>8s}  {m_dir:>4s}  {prods[i]:>7.1f}  {p_ma:>8s}  {p_dir:>4s}")

        # --- 7c. ベスト/ワースト月分析 ---
        print(f"\n  【ベスト/ワースト月分析 ({max_year}年)】")

        best_margin = max(curr_recs, key=lambda r: r.gross_margin)
        worst_margin = min(curr_recs, key=lambda r: r.gross_margin)
        best_prod = max(curr_recs, key=lambda r: r.productivity)
        worst_prod = min(curr_recs, key=lambda r: r.productivity)
        best_rev = max(curr_recs, key=lambda r: r.revenue)
        worst_rev = min(curr_recs, key=lambda r: r.revenue)

        print(f"\n    粗利率:")
        print(f"      ベスト:  {best_margin.period_label} ({pct(best_margin.gross_margin)})")
        print(f"      ワースト: {worst_margin.period_label} ({pct(worst_margin.gross_margin)})")
        _compare_months(best_margin, worst_margin)

        print(f"\n    生産性:")
        print(f"      ベスト:  {best_prod.period_label} (生産性 {best_prod.productivity:.1f})")
        print(f"      ワースト: {worst_prod.period_label} (生産性 {worst_prod.productivity:.1f})")

        print(f"\n    売上:")
        print(f"      ベスト:  {best_rev.period_label} ({fmt(best_rev.revenue)})")
        print(f"      ワースト: {worst_rev.period_label} ({fmt(worst_rev.revenue)})")


def _compare_months(best: MonthlyRecord, worst: MonthlyRecord) -> None:
    """ベスト月とワースト月の違いを分析"""
    print(f"\n      ベスト月 vs ワースト月の違い:")
    print(f"      {'指標':<16s}  {'ベスト':>14s}  {'ワースト':>14s}  {'差':>12s}")
    print(f"      {'─' * 56}")

    comparisons = [
        ("売上", best.revenue, worst.revenue, True),
        ("原価率", best.cost_ratio, worst.cost_ratio, False),
        ("労務費/売上", best.labor_cost_ratio, worst.labor_cost_ratio, False),
        ("スタッフ工数", best.staff_hours, worst.staff_hours, True),
        ("残業率", best.overtime_ratio, worst.overtime_ratio, False),
        ("生産性", best.productivity, worst.productivity, True),
    ]

    for label, bv, wv, is_amount in comparisons:
        if is_amount and isinstance(bv, (int, float)) and bv > 10000:
            print(f"      {label:<14s}  {fmt(int(bv)):>14s}  {fmt(int(wv)):>14s}  {fmt(int(bv - wv)):>12s}")
        else:
            diff = bv - wv
            print(f"      {label:<14s}  {bv:>13.1f}  {wv:>13.1f}  {diff:>+11.1f}")


# ============================================================
# 8. [拡張] データ異常値の自動検出
# ============================================================

def detect_data_anomalies(records: list[MonthlyRecord]) -> None:
    print()
    sep()
    print("  8. データ異常値の自動検出")
    sep()

    sites = group_by_site(records)

    for site_name, recs in sites.items():
        print(f"\n{'─' * 80}")
        print(f"  現場: {site_name}")
        print(f"{'─' * 80}")

        sorted_recs = sort_by_time(recs)
        anomalies = []

        # --- 8a. 統計的異常値検出（平均±2σ） ---
        numeric_fields = [
            ("売上", [r.revenue for r in sorted_recs]),
            ("原価合計", [r.total_cost for r in sorted_recs]),
            ("粗利率", [r.gross_margin for r in sorted_recs]),
            ("労務費", [r.labor_cost for r in sorted_recs]),
            ("給与手当", [r.salary_cost for r in sorted_recs]),
            ("外注費", [r.outsource_cost for r in sorted_recs]),
            ("スタッフ工数", [r.staff_hours for r in sorted_recs]),
            ("タイミー工数", [r.timee_hours for r in sorted_recs]),
            ("社員残業工数", [r.employee_overtime_hours for r in sorted_recs]),
            ("有給", [r.paid_leave for r in sorted_recs]),
            ("生産性", [r.productivity for r in sorted_recs]),
            ("残業率", [r.overtime_ratio for r in sorted_recs]),
        ]

        print(f"\n  【統計的異常値（平均±2σ外）】")
        found_stat = False

        for field_name, values in numeric_fields:
            m = mean(values)
            s = stdev(values)
            if s == 0:
                continue

            for i, (v, r) in enumerate(zip(values, sorted_recs)):
                z_score = (v - m) / s
                if abs(z_score) > 2.0:
                    found_stat = True
                    direction = "異常に高い" if z_score > 0 else "異常に低い"
                    if isinstance(v, float) and v < 1000:
                        val_str = f"{v:.1f}"
                        avg_str = f"{m:.1f}"
                    else:
                        val_str = f"{v:,.0f}"
                        avg_str = f"{m:,.0f}"
                    anomalies.append({
                        "period": r.period_label,
                        "field": field_name,
                        "value": val_str,
                        "mean": avg_str,
                        "z_score": z_score,
                        "direction": direction,
                    })
                    print(f"    {r.period_label}: {field_name}が{direction} (値: {val_str}, 平均: {avg_str}, Z={z_score:+.2f})")

        if not found_stat:
            print("    統計的異常値なし")

        # --- 8b. 前月比の急変検出 ---
        print(f"\n  【前月比急変検出（前月比±50%以上または絶対値急変）】")
        found_spike = False

        spike_fields = [
            ("外注費", lambda r: r.outsource_cost),
            ("タイミー工数", lambda r: r.timee_hours),
            ("有給", lambda r: r.paid_leave),
            ("社員残業工数", lambda r: r.employee_overtime_hours),
            ("タイミー時給", lambda r: r.timee_hourly_cost),
        ]

        for field_name, getter in spike_fields:
            for i in range(1, len(sorted_recs)):
                curr_v = getter(sorted_recs[i])
                prev_v = getter(sorted_recs[i - 1])

                # ゼロから発生
                if prev_v == 0 and curr_v > 0:
                    found_spike = True
                    print(f"    {sorted_recs[i].period_label}: {field_name} が 0 → {curr_v:,.0f} に突然発生")
                # 突然消滅
                elif prev_v > 0 and curr_v == 0:
                    found_spike = True
                    print(f"    {sorted_recs[i].period_label}: {field_name} が {prev_v:,.0f} → 0 に突然消滅")
                # 大幅変動
                elif prev_v > 0:
                    change = (curr_v - prev_v) / prev_v * 100
                    if abs(change) > 200:
                        found_spike = True
                        print(f"    {sorted_recs[i].period_label}: {field_name} が前月比 {change:+.0f}% ({prev_v:,.0f} → {curr_v:,.0f})")

        if not found_spike:
            print("    急変なし")

        # --- 8c. データ整合性チェック ---
        print(f"\n  【データ整合性チェック】")
        found_integrity = False

        for r in sorted_recs:
            # 工数の整合性
            calc_hours = r.employee_regular_hours + r.employee_overtime_hours
            if abs(calc_hours - r.employee_total_hours) > 1.0:
                found_integrity = True
                print(f"    {r.period_label}: 社員工数不整合 (通常{r.employee_regular_hours}h + 残業{r.employee_overtime_hours}h = {calc_hours}h ≠ 総工数{r.employee_total_hours}h)")

            # 単価の整合性
            if r.touch_count > 0 and r.shipments > 0:
                calc_price = r.shipments / r.touch_count
                if abs(calc_price - r.avg_unit_price) > 1.0:
                    found_integrity = True
                    print(f"    {r.period_label}: 平均単価不整合 (出庫{r.shipments:,}/タッチ{r.touch_count:,} = {calc_price:.1f} ≠ 記録値{r.avg_unit_price})")

            # タイミー費用の整合性
            if r.timee_hours > 0 and r.timee_hourly_cost == 0:
                found_integrity = True
                print(f"    {r.period_label}: タイミー工数{r.timee_hours}hあるが時給が0")
            if r.timee_hours == 0 and r.timee_hourly_cost > 0:
                found_integrity = True
                print(f"    {r.period_label}: タイミー工数0だが時給{r.timee_hourly_cost}が記録されている")

            # 異常に高い工数（1日24h×31日×人数を超える）
            max_possible = r.employee_count * 31 * 24
            if r.employee_count > 0 and r.employee_total_hours > max_possible:
                found_integrity = True
                print(f"    {r.period_label}: 社員工数が物理的上限超え ({r.employee_total_hours}h, 社員{r.employee_count}名の上限={max_possible}h)")

            # タイミー工数が総工数の90%以上
            if r.total_hours > 0 and r.timee_hours / r.total_hours > 0.9:
                found_integrity = True
                print(f"    {r.period_label}: タイミー工数が総工数の{r.timee_hours / r.total_hours * 100:.0f}%を占める（{r.timee_hours:,.0f}h / {r.total_hours:,.0f}h）データ入力ミスの可能性")

        if not found_integrity:
            print("    整合性問題なし")

        # --- 8d. サマリ ---
        total_anomalies = len(anomalies) + (1 if found_spike else 0) + (1 if found_integrity else 0)
        if total_anomalies > 0:
            print(f"\n  【異常検出サマリ】")
            print(f"    統計的異常: {len(anomalies)}件")
            print(f"    データの突然の変化: {'あり' if found_spike else 'なし'}")
            print(f"    データ整合性の問題: {'あり' if found_integrity else 'なし'}")
            print(f"\n    ※ これらの異常値はデータ入力ミスまたは実際の業務上の問題の")
            print(f"      いずれかです。まずデータの正確性を確認してください。")


# ============================================================
# 9. 総合所見
# ============================================================

def print_executive_summary(records: list[MonthlyRecord]) -> None:
    print()
    sep("█")
    print("  総合所見・アクションアイテム")
    sep("█")

    sites = group_by_site(records)
    years = sorted(set(r.year for r in records))
    max_year, min_year = max(years), min(years)

    for site_name, recs in sites.items():
        curr_recs = sorted([r for r in recs if r.year == max_year], key=lambda r: r.month)
        prev_recs = sorted([r for r in recs if r.year == min_year], key=lambda r: r.month)

        if not curr_recs or not prev_recs:
            continue

        curr_rev = sum(r.revenue for r in curr_recs)
        prev_rev = sum(r.revenue for r in prev_recs)
        curr_cost = sum(r.total_cost for r in curr_recs)
        prev_cost = sum(r.total_cost for r in prev_recs)
        curr_margin = (curr_rev - curr_cost) / curr_rev * 100 if curr_rev else 0
        prev_margin = (prev_rev - prev_cost) / prev_rev * 100 if prev_rev else 0

        curr_labor = sum(r.labor_cost for r in curr_recs)
        prev_labor = sum(r.labor_cost for r in prev_recs)

        print(f"\n  現場: {site_name}")
        print(f"  {'─' * 70}")

        # 最重要発見事項
        print(f"\n  ■ 最重要発見事項")

        findings = []

        # 増収減益
        if curr_rev > prev_rev and curr_margin < prev_margin:
            findings.append(
                f"増収減益: 売上は{(curr_rev - prev_rev) / prev_rev * 100:+.1f}%伸びているが、"
                f"粗利率は{prev_margin:.1f}%→{curr_margin:.1f}%に悪化。"
                f"「売れば売るほど利益率が下がる」構造になっている。"
            )

        # 労務費の膨張
        labor_growth = (curr_labor - prev_labor) / prev_labor * 100 if prev_labor else 0
        rev_growth = (curr_rev - prev_rev) / prev_rev * 100 if prev_rev else 0
        if labor_growth > rev_growth + 5:
            findings.append(
                f"労務費の膨張: 売上成長率{rev_growth:+.1f}%に対し、労務費成長率は{labor_growth:+.1f}%。"
                f"労務費の伸びが売上の伸びを大きく上回っている。"
            )

        # 生産性の低下トレンド
        prods = [r.productivity for r in curr_recs]
        if len(prods) >= 3 and prods[-1] < prods[0] * 0.7:
            findings.append(
                f"生産性の大幅低下: {max_year}年初の{prods[0]:.0f}から直近{prods[-1]:.0f}へ"
                f"（{(prods[-1] / prods[0] - 1) * 100:+.0f}%）。"
            )

        # 外注費の急増
        curr_out = sum(r.outsource_cost for r in curr_recs)
        prev_out = sum(r.outsource_cost for r in prev_recs)
        if curr_out > prev_out * 3 and curr_out > 1000000:
            findings.append(
                f"外注費の急増: {fmt_man(prev_out)}→{fmt_man(curr_out)}。"
                f"タイミー等の外部人材への依存が拡大している。"
            )

        # 特定月の異常
        worst = min(curr_recs, key=lambda r: r.gross_margin)
        if worst.gross_margin < 15:
            findings.append(
                f"収益危機月: {worst.period_label}の粗利率が{pct(worst.gross_margin)}まで低下。"
                f"原価率{pct(worst.cost_ratio)}で赤字に近い水準。"
            )

        for i, f in enumerate(findings, 1):
            print(f"    {i}. {f}")

        if not findings:
            print(f"    特筆すべき異常はありません。")

        # アクションアイテム
        print(f"\n  ■ 推奨アクション")
        actions = []

        if labor_growth > rev_growth:
            actions.append("労務費の見直し: スタッフ配置の最適化、シフト管理の効率化を検討")
            actions.append("時給と工数の両面を精査し、どちらがコスト増の主因か特定する")

        if curr_out > prev_out * 2:
            actions.append("外注費の精査: タイミー等の利用基準を再設定し、本当に必要な場面に限定する")

        if prods[-1] < 70:
            actions.append("生産性改善: オペレーション見直し、ボトルネック工程の特定")

        avg_ot = mean([r.overtime_ratio for r in curr_recs])
        if avg_ot > 15:
            actions.append(f"残業管理: 平均残業率{pct(avg_ot)}を削減。業務の平準化を検討")

        if curr_margin < 20:
            actions.append(f"価格交渉: 現在の粗利率{pct(curr_margin)}は持続困難。単価見直しまたは管理費の改定を検討")

        actions.append("データ品質: 12月のタイミー工数等、異常値がないか元データを再確認")

        for i, a in enumerate(actions, 1):
            print(f"    {i}. {a}")


# ============================================================
# メイン
# ============================================================

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    filepath = os.path.join(data_dir, "site_financial_data.csv")

    print()
    sep("█")
    print("  物流現場 高度財務分析ツール")
    sep("█")

    records = load_data(filepath)
    sites = set(r.site_name for r in records)
    years = sorted(set(r.year for r in records))
    print(f"  読み込み完了: {len(records)}件 / {len(sites)}現場 / {years[0]}〜{years[-1]}年")

    # 基本分析
    analyze_profitability(records)       # 1. 収益性
    extract_issues(records)              # 2. 課題抽出
    check_kpi_alignment(records)         # 3. KPI整合性

    # 拡張分析
    analyze_cost_structure(records)       # 4. コスト異常検知・要因分解
    analyze_revenue_cost_linkage(records) # 5. 売上原価連動性・損益分岐点
    analyze_productivity_patterns(records)# 6. 生産性劣化パターン
    analyze_multi_angle(records)          # 7. 多角的比較
    detect_data_anomalies(records)        # 8. データ異常値検出

    # 総合所見
    print_executive_summary(records)      # 9. 総合所見

    print()
    sep("█")
    print("  分析完了")
    sep("█")
    print()


if __name__ == "__main__":
    main()
