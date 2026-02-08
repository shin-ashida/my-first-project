"""
物流現場 財務分析ツール

機能:
1. 各現場の収益性を分析（前年比較・月次推移）
2. 現場ごとの課題を数値から抽出
3. 経営KPIと現場KPIの整合性を確認
"""

import csv
import os
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
    revenue: int              # 売上
    shipments: int            # 出庫
    touch_count: int          # タッチ数
    avg_unit_price: float     # 平均単価
    admin_cost: int           # 管理費
    other_revenue: int        # その他売上
    salary_cost: int          # 給与手当（原）
    employee_total_hours: float   # 社員総工数
    employee_regular_hours: float # 社員通常工数
    employee_overtime_hours: float # 社員残業工数
    employee_count: float     # 社員人数
    labor_cost: int           # 労務費
    staff_hours: float        # スタッフ工数
    avg_hourly_wage: int      # 平均時給
    outsource_cost: int       # 外注費（原）
    timee_hours: float        # タイミー工数
    timee_hourly_cost: int    # タイミー時給
    paid_leave: int           # 有給
    statutory_welfare: int    # 法定福利費（原）
    travel_expense: int       # 旅費交通費（原）

    @property
    def period_label(self) -> str:
        return f"{self.year}年{self.month}月"

    @property
    def total_cost(self) -> int:
        """原価合計"""
        return (self.salary_cost + self.labor_cost + self.outsource_cost
                + self.paid_leave + self.statutory_welfare + self.travel_expense)

    @property
    def gross_profit(self) -> int:
        """粗利"""
        return self.revenue - self.total_cost

    @property
    def gross_margin(self) -> float:
        """粗利率（対売上比）"""
        if self.revenue == 0:
            return 0.0
        return self.gross_profit / self.revenue * 100

    @property
    def cost_ratio(self) -> float:
        """原価/売上"""
        if self.revenue == 0:
            return 0.0
        return self.total_cost / self.revenue * 100

    @property
    def labor_cost_ratio(self) -> float:
        """労務費/売上"""
        if self.revenue == 0:
            return 0.0
        return self.labor_cost / self.revenue * 100

    @property
    def total_hours(self) -> float:
        """総工数（社員＋スタッフ＋タイミー）"""
        return self.employee_total_hours + self.staff_hours + self.timee_hours

    @property
    def productivity(self) -> float:
        """生産性: タッチ数 / 総工数"""
        if self.total_hours == 0:
            return 0.0
        return self.touch_count / self.total_hours

    @property
    def revenue_per_employee(self) -> float:
        """社員一人あたり売上"""
        if self.employee_count == 0:
            return 0.0
        return self.revenue / self.employee_count

    @property
    def overtime_ratio(self) -> float:
        """残業率: 残業工数 / 総工数"""
        if self.employee_total_hours == 0:
            return 0.0
        return self.employee_overtime_hours / self.employee_total_hours * 100


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
    """金額をカンマ区切りで表示"""
    return f"¥{amount:,}"


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
    """指定年月のレコードを返す"""
    for r in recs:
        if r.year == year and r.month == month:
            return r
    return None


# ============================================================
# 1. 現場別 収益性分析
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

        # 年ごとの集計
        years = sorted(set(r.year for r in recs))
        for year in years:
            year_recs = [r for r in recs if r.year == year]
            total_rev = sum(r.revenue for r in year_recs)
            total_cost = sum(r.total_cost for r in year_recs)
            total_profit = sum(r.gross_profit for r in year_recs)
            avg_margin = (total_profit / total_rev * 100) if total_rev else 0
            print(f"\n  【{year}年 合計】売上: {fmt(total_rev)} / 原価: {fmt(total_cost)} / 粗利: {fmt(total_profit)} / 粗利率: {pct(avg_margin)}")

        # 月次推移 (前年比較)
        months = sorted(set(r.month for r in recs))
        max_year = max(years)
        min_year = min(years)

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
                yoy_val = (curr.revenue - prev.revenue) / prev.revenue * 100
                yoy = f"{yoy_val:+.1f}%"

            prev_margin = pct(prev.gross_margin) if prev else "-"
            curr_margin = pct(curr.gross_margin) if curr else "-"
            prev_prod = f"{prev.productivity:.1f}" if prev else "-"
            curr_prod = f"{curr.productivity:.1f}" if curr else "-"

            print(f"  {m:>3d}月  {prev_rev:>14s}  {curr_rev:>14s}  {yoy:>8s}  {prev_margin:>10s}  {curr_margin:>10s}  {prev_prod:>10s}  {curr_prod:>10s}")

        # コスト構成
        print(f"\n  【コスト構成比較】")
        for year in years:
            year_recs = [r for r in recs if r.year == year]
            total_c = sum(r.total_cost for r in year_recs)
            total_rev = sum(r.revenue for r in year_recs)
            salary = sum(r.salary_cost for r in year_recs)
            labor = sum(r.labor_cost for r in year_recs)
            outsource = sum(r.outsource_cost for r in year_recs)
            leave = sum(r.paid_leave for r in year_recs)
            welfare = sum(r.statutory_welfare for r in year_recs)
            travel = sum(r.travel_expense for r in year_recs)

            print(f"    {year}年 (原価合計: {fmt(total_c)}, 原価率: {pct(total_c / total_rev * 100 if total_rev else 0)})")
            for label, val in [("給与手当", salary), ("労務費", labor), ("外注費", outsource),
                               ("有給", leave), ("法定福利費", welfare), ("旅費交通費", travel)]:
                ratio = (val / total_c * 100) if total_c else 0
                print(f"      {label:<10s}: {fmt(val):>14s} ({pct(ratio):>6s})")


# ============================================================
# 2. 課題抽出
# ============================================================

# 閾値（これらを経営方針に合わせて調整してください）
THRESHOLDS = {
    "low_gross_margin": 20.0,       # 粗利率がこれ以下で警告
    "high_cost_ratio": 80.0,        # 原価率がこれ以上で警告
    "high_labor_ratio": 55.0,       # 労務費/売上がこれ以上で警告
    "low_productivity": 70,         # 生産性(タッチ数/総工数)がこれ以下で警告
    "productivity_decline": -10.0,  # 生産性前年比がこのポイント以下で警告
    "high_overtime_ratio": 15.0,    # 残業率がこれ以上で警告
    "revenue_decline": -5.0,        # 売上前年比がこれ以下で警告
    "margin_decline": -5.0,         # 粗利率前年差がこのポイント以下で警告
}


def extract_issues(records: list[MonthlyRecord]) -> None:
    print()
    sep()
    print("  2. 現場ごとの課題抽出")
    sep()

    sites = group_by_site(records)
    years = sorted(set(r.year for r in records))
    max_year = max(years)
    min_year = min(years)

    for site_name, recs in sites.items():
        issues = []

        months = sorted(set(r.month for r in recs))
        for m in months:
            curr = find_pair(recs, max_year, m)
            prev = find_pair(recs, min_year, m)
            if not curr:
                continue

            label = f"{max_year}年{m}月"

            # 粗利率低下
            if curr.gross_margin < THRESHOLDS["low_gross_margin"]:
                sev = "HIGH" if curr.gross_margin < 15 else "MEDIUM"
                issues.append((sev, "収益性", label,
                               f"粗利率 {pct(curr.gross_margin)} (基準: {pct(THRESHOLDS['low_gross_margin'])}以上)"))

            # 原価率高騰
            if curr.cost_ratio > THRESHOLDS["high_cost_ratio"]:
                sev = "HIGH" if curr.cost_ratio > 85 else "MEDIUM"
                issues.append((sev, "コスト", label,
                               f"原価率 {pct(curr.cost_ratio)} (基準: {pct(THRESHOLDS['high_cost_ratio'])}以下)"))

            # 労務費比率
            if curr.labor_cost_ratio > THRESHOLDS["high_labor_ratio"]:
                sev = "HIGH" if curr.labor_cost_ratio > 60 else "MEDIUM"
                issues.append((sev, "人件費", label,
                               f"労務費/売上 {pct(curr.labor_cost_ratio)} (基準: {pct(THRESHOLDS['high_labor_ratio'])}以下)"))

            # 生産性低下
            if curr.productivity < THRESHOLDS["low_productivity"]:
                sev = "HIGH" if curr.productivity < 60 else "MEDIUM"
                issues.append((sev, "生産性", label,
                               f"生産性 {curr.productivity:.1f} (基準: {THRESHOLDS['low_productivity']}以上)"))

            # 生産性前年比
            if prev and prev.productivity > 0:
                prod_change = ((curr.productivity - prev.productivity) / prev.productivity) * 100
                if prod_change < THRESHOLDS["productivity_decline"]:
                    sev = "HIGH" if prod_change < -20 else "MEDIUM"
                    issues.append((sev, "生産性", label,
                                   f"生産性前年比 {prod_change:+.1f}% (基準: {THRESHOLDS['productivity_decline']}%以上)"))

            # 残業率
            if curr.overtime_ratio > THRESHOLDS["high_overtime_ratio"]:
                sev = "HIGH" if curr.overtime_ratio > 20 else "MEDIUM"
                issues.append((sev, "労務", label,
                               f"残業率 {pct(curr.overtime_ratio)} (基準: {pct(THRESHOLDS['high_overtime_ratio'])}以下)"))

            # 売上前年比
            if prev and prev.revenue > 0:
                rev_change = (curr.revenue - prev.revenue) / prev.revenue * 100
                if rev_change < THRESHOLDS["revenue_decline"]:
                    issues.append(("MEDIUM", "売上", label,
                                   f"売上前年比 {rev_change:+.1f}% (基準: {THRESHOLDS['revenue_decline']}%以上)"))

            # 粗利率前年差
            if prev:
                margin_diff = curr.gross_margin - prev.gross_margin
                if margin_diff < THRESHOLDS["margin_decline"]:
                    sev = "HIGH" if margin_diff < -10 else "MEDIUM"
                    issues.append((sev, "収益性", label,
                                   f"粗利率前年差 {margin_diff:+.1f}pt (前年{pct(prev.gross_margin)}→今年{pct(curr.gross_margin)})"))

        # 表示
        high_count = sum(1 for i in issues if i[0] == "HIGH")
        med_count = sum(1 for i in issues if i[0] == "MEDIUM")

        if high_count > 0:
            status = "要改善"
        elif med_count > 0:
            status = "要注意"
        else:
            status = "良好"

        print(f"\n  [{status}] {site_name} - HIGH: {high_count}件 / MEDIUM: {med_count}件")
        print(f"  {'─' * 70}")

        if not issues:
            print("    全指標が基準値内です。")
        else:
            for sev, cat, period, desc in issues:
                mark = "!!" if sev == "HIGH" else "! "
                print(f"    {mark} [{cat}] {period}: {desc}")

        # サマリ
        if issues:
            categories = {}
            for sev, cat, _, _ in issues:
                categories.setdefault(cat, {"HIGH": 0, "MEDIUM": 0})
                categories[cat][sev] += 1
            print(f"\n    課題サマリ:")
            for cat, counts in sorted(categories.items(), key=lambda x: x[1]["HIGH"], reverse=True):
                print(f"      {cat}: HIGH {counts['HIGH']}件, MEDIUM {counts['MEDIUM']}件")


# ============================================================
# 3. 経営KPI と 現場KPI の整合性チェック
# ============================================================

# 経営KPI目標値（ここを自社の目標に合わせて変更してください）
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
    max_year = max(years)
    min_year = min(years)

    for site_name, recs in sites.items():
        print(f"\n{'─' * 80}")
        print(f"  現場: {site_name}")
        print(f"{'─' * 80}")

        curr_recs = [r for r in recs if r.year == max_year]
        prev_recs = [r for r in recs if r.year == min_year]

        if not curr_recs:
            print("    今年度のデータがありません。")
            continue

        # 実績算出
        curr_rev = sum(r.revenue for r in curr_recs)
        curr_cost = sum(r.total_cost for r in curr_recs)
        curr_labor = sum(r.labor_cost for r in curr_recs)
        curr_touch = sum(r.touch_count for r in curr_recs)
        curr_hours = sum(r.total_hours for r in curr_recs)
        curr_emp_count = sum(r.employee_count for r in curr_recs) / len(curr_recs)  # 平均
        curr_ot_hours = sum(r.employee_overtime_hours for r in curr_recs)
        curr_emp_hours = sum(r.employee_total_hours for r in curr_recs)

        prev_rev = sum(r.revenue for r in prev_recs) if prev_recs else 0

        actuals = {
            "粗利率": ((curr_rev - curr_cost) / curr_rev * 100) if curr_rev else 0,
            "原価率": (curr_cost / curr_rev * 100) if curr_rev else 0,
            "労務費比率": (curr_labor / curr_rev * 100) if curr_rev else 0,
            "生産性(タッチ/時間)": (curr_touch / curr_hours) if curr_hours else 0,
            "社員一人あたり売上": (curr_rev / curr_emp_count) if curr_emp_count else 0,
            "残業率": (curr_ot_hours / curr_emp_hours * 100) if curr_emp_hours else 0,
            "売上前年成長率": ((curr_rev - prev_rev) / prev_rev * 100) if prev_rev else 0,
        }

        # 判定
        ok_count = 0
        ng_count = 0
        print(f"\n  {'KPI名':<22s}  {'目標':>12s}  {'実績':>12s}  {'判定':>4s}  {'乖離':>10s}")
        print(f"  {'─' * 68}")

        for kpi_name, target_info in MANAGEMENT_KPIS.items():
            target = target_info["target"]
            unit = target_info["unit"]
            direction = target_info["direction"]
            actual = actuals.get(kpi_name, 0)

            if direction == "higher":
                met = actual >= target
                gap = actual - target
            else:
                met = actual <= target
                gap = target - actual

            mark = "OK" if met else "NG"
            if met:
                ok_count += 1
            else:
                ng_count += 1

            if kpi_name == "社員一人あたり売上":
                target_str = f"{fmt(int(target))}"
                actual_str = f"{fmt(int(actual))}"
                gap_str = f"{fmt(int(gap))}"
            else:
                target_str = f"{target:.1f}{unit}"
                actual_str = f"{actual:.1f}{unit}"
                gap_str = f"{gap:+.1f}{unit}"

            print(f"  {kpi_name:<20s}  {target_str:>12s}  {actual_str:>12s}  [{mark}]  {gap_str:>10s}")

        total = ok_count + ng_count
        rate = (ok_count / total * 100) if total else 0
        bar = "■" * int(rate / 5) + "□" * (20 - int(rate / 5))
        print(f"\n  KPI達成率: {ok_count}/{total} ({rate:.0f}%) [{bar}]")

        # 月次でのKPI推移（粗利率と生産性のみ）
        months = sorted(set(r.month for r in curr_recs))
        print(f"\n  【月次KPI推移 ({max_year}年)】")
        print(f"  {'月':>4s}  {'粗利率':>8s}  {'目標':>6s}  {'判定':>4s}  {'生産性':>8s}  {'目標':>6s}  {'判定':>4s}  {'残業率':>8s}  {'目標':>6s}  {'判定':>4s}")
        print(f"  {'─' * 72}")

        for m in months:
            r = find_pair(curr_recs, max_year, m)
            if not r:
                continue

            gm = r.gross_margin
            gm_ok = "OK" if gm >= MANAGEMENT_KPIS["粗利率"]["target"] else "NG"
            pr = r.productivity
            pr_ok = "OK" if pr >= MANAGEMENT_KPIS["生産性(タッチ/時間)"]["target"] else "NG"
            ot = r.overtime_ratio
            ot_ok = "OK" if ot <= MANAGEMENT_KPIS["残業率"]["target"] else "NG"

            print(f"  {m:>3d}月  {pct(gm):>8s}  {pct(MANAGEMENT_KPIS['粗利率']['target']):>6s}  [{gm_ok}]  {pr:>7.1f}  {MANAGEMENT_KPIS['生産性(タッチ/時間)']['target']:>5.0f}  [{pr_ok}]  {pct(ot):>8s}  {pct(MANAGEMENT_KPIS['残業率']['target']):>6s}  [{ot_ok}]")

    # 全体所見
    print(f"\n{'═' * 80}")
    if ng_count == 0:
        print("  【所見】全KPIが目標を達成しています。")
    elif ng_count <= 2:
        print("  【所見】概ね良好ですが、一部KPIに改善の余地があります。")
    elif ng_count <= 4:
        print("  【所見】複数のKPIが未達です。重点的な改善施策が必要です。")
    else:
        print("  【所見】多くのKPIが未達です。コスト構造・生産性の抜本的な見直しを推奨します。")


# ============================================================
# メイン
# ============================================================

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    filepath = os.path.join(data_dir, "site_financial_data.csv")

    print()
    sep()
    print("  物流現場 財務分析ツール")
    sep()

    records = load_data(filepath)
    sites = set(r.site_name for r in records)
    years = sorted(set(r.year for r in records))
    print(f"  読み込み完了: {len(records)}件 / {len(sites)}現場 / {years[0]}〜{years[-1]}年")

    # 1. 収益性分析
    analyze_profitability(records)

    # 2. 課題抽出
    extract_issues(records)

    # 3. KPI整合性
    check_kpi_alignment(records)

    print()
    sep()
    print("  分析完了")
    sep()
    print()


if __name__ == "__main__":
    main()
