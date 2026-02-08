"""
現場別 財務分析ツール

機能:
1. 各現場の収益性を分析
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
class SiteRecord:
    """現場ごとの四半期財務データ"""
    site_id: str
    site_name: str
    period: str
    revenue: int
    material_cost: int
    labor_cost: int
    subcontract_cost: int
    overhead_cost: int
    budget_revenue: int
    budget_cost: int
    planned_days: int
    actual_days: int
    workers_planned: int
    workers_actual: int
    safety_incidents: int
    rework_count: int
    client_satisfaction: float

    @property
    def total_cost(self) -> int:
        return self.material_cost + self.labor_cost + self.subcontract_cost + self.overhead_cost

    @property
    def gross_profit(self) -> int:
        return self.revenue - self.total_cost

    @property
    def gross_profit_margin(self) -> float:
        if self.revenue == 0:
            return 0.0
        return (self.gross_profit / self.revenue) * 100

    @property
    def budget_achievement_rate(self) -> float:
        if self.budget_revenue == 0:
            return 0.0
        return (self.revenue / self.budget_revenue) * 100

    @property
    def cost_overrun_rate(self) -> float:
        if self.budget_cost == 0:
            return 0.0
        return (self.total_cost / self.budget_cost) * 100

    @property
    def schedule_adherence_rate(self) -> float:
        if self.planned_days == 0:
            return 0.0
        return (self.actual_days / self.planned_days) * 100

    @property
    def labor_productivity(self) -> float:
        if self.workers_actual == 0:
            return 0.0
        return self.revenue / self.workers_actual


@dataclass
class KpiTarget:
    """経営KPI目標値"""
    kpi_name: str
    target_value: float
    unit: str
    direction: str  # higher_is_better / lower_is_better
    weight: float
    category: str


# ============================================================
# データ読み込み
# ============================================================

def load_site_data(filepath: str) -> list[SiteRecord]:
    records = []
    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(SiteRecord(
                site_id=row["site_id"],
                site_name=row["site_name"],
                period=row["period"],
                revenue=int(row["revenue"]),
                material_cost=int(row["material_cost"]),
                labor_cost=int(row["labor_cost"]),
                subcontract_cost=int(row["subcontract_cost"]),
                overhead_cost=int(row["overhead_cost"]),
                budget_revenue=int(row["budget_revenue"]),
                budget_cost=int(row["budget_cost"]),
                planned_days=int(row["planned_days"]),
                actual_days=int(row["actual_days"]),
                workers_planned=int(row["workers_planned"]),
                workers_actual=int(row["workers_actual"]),
                safety_incidents=int(row["safety_incidents"]),
                rework_count=int(row["rework_count"]),
                client_satisfaction=float(row["client_satisfaction"]),
            ))
    return records


def load_kpi_targets(filepath: str) -> list[KpiTarget]:
    targets = []
    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            targets.append(KpiTarget(
                kpi_name=row["kpi_name"],
                target_value=float(row["target_value"]),
                unit=row["unit"],
                direction=row["direction"],
                weight=float(row["weight"]),
                category=row["category"],
            ))
    return targets


# ============================================================
# 1. 現場別 収益性分析
# ============================================================

def analyze_profitability(records: list[SiteRecord]) -> dict:
    """現場ごとの収益性を集計・分析する"""
    sites: dict[str, list[SiteRecord]] = {}
    for r in records:
        sites.setdefault(r.site_id, []).append(r)

    results = {}
    for site_id, recs in sites.items():
        total_revenue = sum(r.revenue for r in recs)
        total_cost = sum(r.total_cost for r in recs)
        total_profit = total_revenue - total_cost
        margin = (total_profit / total_revenue * 100) if total_revenue else 0

        quarterly = []
        for r in recs:
            quarterly.append({
                "period": r.period,
                "revenue": r.revenue,
                "cost": r.total_cost,
                "profit": r.gross_profit,
                "margin": round(r.gross_profit_margin, 1),
                "budget_achievement": round(r.budget_achievement_rate, 1),
            })

        cost_breakdown = {
            "material": sum(r.material_cost for r in recs),
            "labor": sum(r.labor_cost for r in recs),
            "subcontract": sum(r.subcontract_cost for r in recs),
            "overhead": sum(r.overhead_cost for r in recs),
        }

        results[site_id] = {
            "site_name": recs[0].site_name,
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "total_profit": total_profit,
            "profit_margin": round(margin, 1),
            "quarterly": quarterly,
            "cost_breakdown": cost_breakdown,
        }

    return results


# ============================================================
# 2. 現場ごとの課題抽出
# ============================================================

THRESHOLDS = {
    "low_margin": 20.0,           # 粗利率がこれ以下で警告
    "cost_overrun": 105.0,        # 予算超過率がこれ以上で警告
    "schedule_delay": 105.0,      # 工期遅延率がこれ以上で警告
    "high_rework": 2,             # 手直し件数がこれ以上で警告
    "safety_alert": 1,            # 安全事故がこれ以上で警告
    "low_satisfaction": 4.0,      # 顧客満足度がこれ以下で警告
    "labor_overrun": 110.0,       # 人員超過率がこれ以上で警告
}


def extract_issues(records: list[SiteRecord]) -> dict:
    """現場ごとに数値データから課題を抽出する"""
    sites: dict[str, list[SiteRecord]] = {}
    for r in records:
        sites.setdefault(r.site_id, []).append(r)

    all_issues = {}
    for site_id, recs in sites.items():
        issues = []
        for r in recs:
            period = r.period

            # 収益性の課題
            if r.gross_profit_margin < THRESHOLDS["low_margin"]:
                issues.append({
                    "period": period,
                    "category": "収益性",
                    "severity": "HIGH" if r.gross_profit_margin < 10 else "MEDIUM",
                    "description": f"粗利率 {r.gross_profit_margin:.1f}% (基準: {THRESHOLDS['low_margin']}%以上)",
                    "value": round(r.gross_profit_margin, 1),
                })

            # コスト超過
            if r.cost_overrun_rate > THRESHOLDS["cost_overrun"]:
                issues.append({
                    "period": period,
                    "category": "コスト",
                    "severity": "HIGH" if r.cost_overrun_rate > 120 else "MEDIUM",
                    "description": f"予算超過率 {r.cost_overrun_rate:.1f}% (基準: {THRESHOLDS['cost_overrun']}%以下)",
                    "value": round(r.cost_overrun_rate, 1),
                })

            # 工期遅延
            if r.schedule_adherence_rate > THRESHOLDS["schedule_delay"]:
                issues.append({
                    "period": period,
                    "category": "工期",
                    "severity": "HIGH" if r.schedule_adherence_rate > 115 else "MEDIUM",
                    "description": f"工期遅延率 {r.schedule_adherence_rate:.1f}% (基準: {THRESHOLDS['schedule_delay']}%以下)",
                    "value": round(r.schedule_adherence_rate, 1),
                })

            # 手直し
            if r.rework_count >= THRESHOLDS["high_rework"]:
                issues.append({
                    "period": period,
                    "category": "品質",
                    "severity": "HIGH" if r.rework_count >= 4 else "MEDIUM",
                    "description": f"手直し {r.rework_count}件 (基準: {THRESHOLDS['high_rework']}件未満)",
                    "value": r.rework_count,
                })

            # 安全
            if r.safety_incidents >= THRESHOLDS["safety_alert"]:
                issues.append({
                    "period": period,
                    "category": "安全",
                    "severity": "HIGH" if r.safety_incidents >= 2 else "MEDIUM",
                    "description": f"安全事故 {r.safety_incidents}件",
                    "value": r.safety_incidents,
                })

            # 顧客満足度
            if r.client_satisfaction < THRESHOLDS["low_satisfaction"]:
                issues.append({
                    "period": period,
                    "category": "顧客満足",
                    "severity": "HIGH" if r.client_satisfaction < 3.5 else "MEDIUM",
                    "description": f"顧客満足度 {r.client_satisfaction} (基準: {THRESHOLDS['low_satisfaction']}以上)",
                    "value": r.client_satisfaction,
                })

            # 人員超過
            worker_rate = (r.workers_actual / r.workers_planned * 100) if r.workers_planned else 0
            if worker_rate > THRESHOLDS["labor_overrun"]:
                issues.append({
                    "period": period,
                    "category": "人員",
                    "severity": "MEDIUM",
                    "description": f"人員超過率 {worker_rate:.1f}% (計画{r.workers_planned}名→実績{r.workers_actual}名)",
                    "value": round(worker_rate, 1),
                })

        all_issues[site_id] = {
            "site_name": recs[0].site_name,
            "issues": issues,
            "high_count": sum(1 for i in issues if i["severity"] == "HIGH"),
            "medium_count": sum(1 for i in issues if i["severity"] == "MEDIUM"),
        }

    return all_issues


# ============================================================
# 3. 経営KPI と 現場KPI の整合性チェック
# ============================================================

def check_kpi_alignment(records: list[SiteRecord], targets: list[KpiTarget]) -> dict:
    """経営KPIの目標と現場実績を比較し、整合性を評価する"""
    target_map = {t.kpi_name: t for t in targets}

    sites: dict[str, list[SiteRecord]] = {}
    for r in records:
        sites.setdefault(r.site_id, []).append(r)

    # 全社集計
    all_records = records
    company_kpis = _calc_kpis(all_records)

    # 現場別KPI
    site_kpis = {}
    for site_id, recs in sites.items():
        site_kpis[site_id] = {
            "site_name": recs[0].site_name,
            "kpis": _calc_kpis(recs),
        }

    # 整合性判定
    alignment_results = []
    total_score = 0.0

    for kpi_name, target in target_map.items():
        actual = company_kpis.get(kpi_name, 0.0)
        gap = actual - target.target_value
        if target.direction == "lower_is_better":
            gap = -gap  # lower_is_better の場合、実績が低い方が良い

        is_met = gap >= 0
        score = target.weight if is_met else max(0, target.weight * (1 + gap / abs(target.target_value)) if target.target_value != 0 else 0)
        total_score += score

        # 現場別乖離
        site_gaps = []
        for site_id, sk in site_kpis.items():
            site_val = sk["kpis"].get(kpi_name, 0.0)
            site_gap = site_val - target.target_value
            if target.direction == "lower_is_better":
                site_gap = -site_gap
            site_gaps.append({
                "site_id": site_id,
                "site_name": sk["site_name"],
                "value": round(site_val, 2),
                "gap": round(site_gap, 2),
                "met": site_gap >= 0,
            })

        alignment_results.append({
            "kpi_name": kpi_name,
            "category": target.category,
            "target": target.target_value,
            "actual": round(actual, 2),
            "unit": target.unit,
            "direction": target.direction,
            "met": is_met,
            "gap": round(gap, 2),
            "weight": target.weight,
            "score": round(score, 4),
            "site_details": site_gaps,
        })

    return {
        "total_score": round(total_score, 4),
        "max_score": 1.0,
        "achievement_rate": round(total_score * 100, 1),
        "kpi_results": alignment_results,
        "site_kpis": site_kpis,
    }


def _calc_kpis(records: list[SiteRecord]) -> dict:
    """レコード群からKPI値を算出する"""
    total_revenue = sum(r.revenue for r in records)
    total_cost = sum(r.total_cost for r in records)
    total_budget_revenue = sum(r.budget_revenue for r in records)
    total_workers = sum(r.workers_actual for r in records)
    total_planned_days = sum(r.planned_days for r in records)
    total_actual_days = sum(r.actual_days for r in records)
    total_incidents = sum(r.safety_incidents for r in records)
    total_rework = sum(r.rework_count for r in records)
    n = len(records)

    gross_margin = ((total_revenue - total_cost) / total_revenue * 100) if total_revenue else 0
    # operating_profit_margin は overhead を除いた形で近似
    direct_cost = sum(r.material_cost + r.labor_cost + r.subcontract_cost for r in records)
    operating_margin = ((total_revenue - direct_cost) / total_revenue * 100) if total_revenue else 0

    return {
        "gross_profit_margin": round(gross_margin, 2),
        "operating_profit_margin": round(operating_margin, 2),
        "budget_achievement_rate": round((total_revenue / total_budget_revenue * 100) if total_budget_revenue else 0, 2),
        "schedule_adherence_rate": round((total_actual_days / total_planned_days * 100) if total_planned_days else 0, 2),
        "labor_productivity": round(total_revenue / total_workers if total_workers else 0, 0),
        "safety_incident_rate": round(total_incidents / (n / 3) if n else 0, 2),  # 四半期あたり
        "rework_rate": round(total_rework / n * 100 / 10 if n else 0, 2),  # 概算%
        "client_satisfaction": round(sum(r.client_satisfaction for r in records) / n if n else 0, 2),
    }


# ============================================================
# レポート出力
# ============================================================

def fmt_yen(amount: int) -> str:
    """金額を万円単位で表示"""
    return f"{amount / 10000:,.0f}万円"


def print_separator(char: str = "=", width: int = 70):
    print(char * width)


def print_profitability_report(results: dict):
    print()
    print_separator()
    print("  1. 現場別 収益性分析レポート")
    print_separator()

    # 全体サマリ
    total_rev = sum(v["total_revenue"] for v in results.values())
    total_prof = sum(v["total_profit"] for v in results.values())
    overall_margin = (total_prof / total_rev * 100) if total_rev else 0
    print(f"\n【全社サマリ】売上合計: {fmt_yen(total_rev)} / 利益合計: {fmt_yen(total_prof)} / 粗利率: {overall_margin:.1f}%")

    # ランキング
    ranked = sorted(results.items(), key=lambda x: x[1]["profit_margin"], reverse=True)
    print("\n  現場名                          粗利率    売上累計        利益累計")
    print("  " + "-" * 66)
    for site_id, data in ranked:
        name = data["site_name"].ljust(20, "\u3000")
        print(f"  {name}  {data['profit_margin']:>6.1f}%  {fmt_yen(data['total_revenue']):>14s}  {fmt_yen(data['total_profit']):>14s}")

    # 各現場詳細
    for site_id, data in ranked:
        print(f"\n  --- {data['site_name']} ({site_id}) ---")
        cb = data["cost_breakdown"]
        total_c = sum(cb.values())
        for label, key in [("材料費", "material"), ("労務費", "labor"), ("外注費", "subcontract"), ("経費", "overhead")]:
            ratio = (cb[key] / total_c * 100) if total_c else 0
            print(f"    {label}: {fmt_yen(cb[key]):>12s} ({ratio:>5.1f}%)")
        print(f"    四半期推移:")
        for q in data["quarterly"]:
            print(f"      {q['period']}: 粗利率 {q['margin']:>5.1f}% / 予算達成率 {q['budget_achievement']:>5.1f}%")


def print_issues_report(issues: dict):
    print()
    print_separator()
    print("  2. 現場ごとの課題抽出レポート")
    print_separator()

    # 課題の多い順にソート
    ranked = sorted(issues.items(), key=lambda x: (x[1]["high_count"], x[1]["medium_count"]), reverse=True)

    for site_id, data in ranked:
        high = data["high_count"]
        med = data["medium_count"]
        total = high + med
        if total == 0:
            status = "良好"
        elif high == 0:
            status = "要注意"
        else:
            status = "要改善"

        print(f"\n  [{status}] {data['site_name']} ({site_id}) - HIGH: {high}件 / MEDIUM: {med}件")

        if not data["issues"]:
            print("    課題なし - 全指標が基準値内です")
            continue

        for issue in data["issues"]:
            sev_mark = "!!" if issue["severity"] == "HIGH" else "! "
            print(f"    {sev_mark} [{issue['category']}] {issue['period']}: {issue['description']}")


def print_kpi_alignment_report(alignment: dict):
    print()
    print_separator()
    print("  3. 経営KPI と 現場KPI の整合性レポート")
    print_separator()

    rate = alignment["achievement_rate"]
    score_bar = "■" * int(rate / 5) + "□" * (20 - int(rate / 5))
    print(f"\n  【総合KPIスコア】 {rate:.1f}% [{score_bar}]")

    # カテゴリ別
    categories = {}
    for kr in alignment["kpi_results"]:
        categories.setdefault(kr["category"], []).append(kr)

    for cat, kpis in categories.items():
        cat_label = {"profitability": "収益性", "efficiency": "効率性", "safety": "安全性", "quality": "品質"}.get(cat, cat)
        print(f"\n  [{cat_label}]")
        for kpi in kpis:
            mark = "OK" if kpi["met"] else "NG"
            kpi_label = {
                "gross_profit_margin": "粗利率",
                "operating_profit_margin": "営業利益率",
                "budget_achievement_rate": "予算達成率",
                "schedule_adherence_rate": "工期遵守率",
                "labor_productivity": "労働生産性",
                "safety_incident_rate": "安全事故率",
                "rework_rate": "手直し率",
                "client_satisfaction": "顧客満足度",
            }.get(kpi["kpi_name"], kpi["kpi_name"])

            print(f"    [{mark}] {kpi_label}: 目標 {kpi['target']}{kpi['unit']} → 実績 {kpi['actual']}{kpi['unit']} (乖離: {kpi['gap']:+.2f})")

            # 現場別で目標未達のものを表示
            unmet = [s for s in kpi["site_details"] if not s["met"]]
            if unmet:
                for s in unmet:
                    print(f"         未達: {s['site_name']} ({s['value']}{kpi['unit']}, 乖離 {s['gap']:+.2f})")

    # 全体所見
    print(f"\n  {'=' * 50}")
    if rate >= 80:
        print("  【所見】経営KPIと現場KPIは概ね整合しています。")
    elif rate >= 60:
        print("  【所見】一部のKPIに乖離があります。重点改善が必要です。")
    else:
        print("  【所見】経営KPIと現場KPIに大きな乖離があります。戦略の見直しを推奨します。")


# ============================================================
# メイン
# ============================================================

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")

    site_data_path = os.path.join(data_dir, "site_financial_data.csv")
    kpi_targets_path = os.path.join(data_dir, "management_kpi_targets.csv")

    print("\n現場別 財務分析ツール")
    print("=" * 70)

    # データ読み込み
    records = load_site_data(site_data_path)
    targets = load_kpi_targets(kpi_targets_path)
    print(f"読み込み完了: {len(records)}件のデータ, {len(targets)}件のKPI目標")

    # 1. 収益性分析
    profitability = analyze_profitability(records)
    print_profitability_report(profitability)

    # 2. 課題抽出
    issues = extract_issues(records)
    print_issues_report(issues)

    # 3. KPI整合性チェック
    alignment = check_kpi_alignment(records, targets)
    print_kpi_alignment_report(alignment)

    print("\n" + "=" * 70)
    print("分析完了")
    print("=" * 70)


if __name__ == "__main__":
    main()
