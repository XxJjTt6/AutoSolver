#!/usr/bin/env python3
"""Render the publication-style AutoSolver system architecture figure."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch


INK = "#1F2937"
MUTED = "#5F6B78"
LINE = "#AEB8C2"
BLUE = "#2E5D8C"
BLUE_LIGHT = "#EDF3F8"
TEAL = "#2B7A78"
TEAL_LIGHT = "#EAF4F2"
GOLD = "#A87326"
GOLD_LIGHT = "#FBF4E8"
GREEN = "#39775A"
GREEN_LIGHT = "#EDF6F0"
RED = "#A65450"
RED_LIGHT = "#FAEFEE"
NEUTRAL = "#F5F7F9"
WHITE = "#FFFFFF"


mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": [
            "PingFang SC",
            "Hiragino Sans GB",
            "Arial",
            "Helvetica",
            "Microsoft YaHei",
            "Noto Sans CJK SC",
            "DejaVu Sans",
        ],
        # Outline text in SVG so GitHub renders the same figure on every OS.
        "svg.fonttype": "path",
        "pdf.fonttype": 42,
        "font.size": 9,
        "axes.linewidth": 0.8,
        "figure.facecolor": WHITE,
        "savefig.facecolor": WHITE,
    }
)


def add_box(
    ax,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    facecolor: str,
    edgecolor: str,
    title: str,
    body: str = "",
    title_color: str = INK,
    body_color: str = MUTED,
    linewidth: float = 1.25,
    radius: float = 0.9,
    title_size: float = 9.2,
    body_size: float = 7.7,
    zorder: int = 3,
) -> None:
    """Draw a restrained rounded rectangle with direct labels."""
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle=f"round,pad=0.22,rounding_size={radius}",
        linewidth=linewidth,
        edgecolor=edgecolor,
        facecolor=facecolor,
        zorder=zorder,
    )
    ax.add_patch(patch)
    body_lines = body.count("\n") + 1 if body else 0
    body_ratio = 0.32 if body_lines >= 4 else 0.37
    body_y = y + height * (body_ratio if body else 0.50)
    ax.text(
        x + width / 2,
        y + height * (0.66 if body else 0.50),
        title,
        ha="center",
        va="center",
        fontsize=title_size,
        fontweight=600,
        color=title_color,
        linespacing=1.12,
        zorder=zorder + 1,
    )
    if body:
        ax.text(
            x + width / 2,
            body_y,
            body,
            ha="center",
            va="center",
            fontsize=body_size,
            color=body_color,
            linespacing=1.28,
            zorder=zorder + 1,
        )


def add_container(
    ax,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    number: str,
    title: str,
    subtitle: str,
    edgecolor: str,
    facecolor: str,
) -> None:
    """Draw a system-layer container with a numbered academic panel header."""
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.28,rounding_size=1.2",
        linewidth=1.35,
        edgecolor=edgecolor,
        facecolor=facecolor,
        zorder=1,
    )
    ax.add_patch(patch)
    ax.text(
        x + 2.0,
        y + height - 3.0,
        number,
        ha="center",
        va="center",
        fontsize=8.6,
        fontweight=600,
        color=WHITE,
        bbox={"boxstyle": "round,pad=0.32,rounding_size=0.55", "fc": edgecolor, "ec": edgecolor},
        zorder=4,
    )
    ax.text(
        x + 4.4,
        y + height - 2.4,
        title,
        ha="left",
        va="center",
        fontsize=10.5,
        fontweight=600,
        color=INK,
        zorder=4,
    )
    ax.text(
        x + 4.4,
        y + height - 4.7,
        subtitle,
        ha="left",
        va="center",
        fontsize=7.2,
        color=MUTED,
        zorder=4,
    )


def add_arrow(
    ax,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = MUTED,
    linewidth: float = 1.35,
    style: str = "-",
    connectionstyle: str = "arc3,rad=0",
    label: str | None = None,
    label_xy: tuple[float, float] | None = None,
    zorder: int = 6,
) -> None:
    """Draw a crisp directional connector with an optional direct label."""
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=11,
        linewidth=linewidth,
        linestyle=style,
        color=color,
        connectionstyle=connectionstyle,
        shrinkA=1.5,
        shrinkB=1.5,
        zorder=zorder,
    )
    ax.add_patch(arrow)
    if label and label_xy:
        ax.text(
            label_xy[0],
            label_xy[1],
            label,
            ha="center",
            va="center",
            fontsize=7.0,
            color=color,
            bbox={"boxstyle": "round,pad=0.18", "fc": WHITE, "ec": "none", "alpha": 0.96},
            zorder=zorder + 1,
        )


def add_elbow_arrow(
    ax,
    vertices: list[tuple[float, float]],
    *,
    color: str,
    linewidth: float = 1.15,
    style: str = "--",
    label: str | None = None,
    label_xy: tuple[float, float] | None = None,
) -> None:
    """Draw a routed connector that avoids the main evidence path."""
    codes = [MplPath.MOVETO] + [MplPath.LINETO] * (len(vertices) - 1)
    path = MplPath(vertices, codes)
    line = PathPatch(
        path,
        fill=False,
        edgecolor=color,
        linewidth=linewidth,
        linestyle=style,
        capstyle="round",
        joinstyle="round",
        zorder=2,
    )
    ax.add_patch(line)
    add_arrow(
        ax,
        vertices[-2],
        vertices[-1],
        color=color,
        linewidth=linewidth,
        style=style,
        zorder=3,
    )
    if label and label_xy:
        ax.text(
            label_xy[0],
            label_xy[1],
            label,
            ha="center",
            va="center",
            fontsize=6.9,
            color=color,
            bbox={"boxstyle": "round,pad=0.18", "fc": WHITE, "ec": "none", "alpha": 0.96},
            zorder=5,
        )


def draw_figure() -> plt.Figure:
    """Build the schematic-led composite at double-column journal width."""
    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 75)
    ax.axis("off")

    # Figure title and publication-style identifier.
    ax.text(2.5, 72.1, "AutoSolver 系统架构", fontsize=17, fontweight=600, color=INK, va="center")
    ax.text(
        2.5,
        68.8,
        "Evidence-gated anytime optimization for courier-task assignment",
        fontsize=8.8,
        color=MUTED,
        va="center",
    )
    ax.text(
        97.5,
        71.9,
        "MEITUAN AI HACKATHON 2026  ·  TASK 04",
        fontsize=7.0,
        color=BLUE,
        fontweight=600,
        ha="right",
        va="center",
    )
    ax.plot([2.5, 97.5], [66.7, 66.7], color="#D7DEE5", linewidth=0.9)

    # Main system layers.
    add_container(
        ax,
        2.5,
        34.5,
        18.0,
        27.5,
        number="01",
        title="问题输入",
        subtitle="Problem instance",
        edgecolor=BLUE,
        facecolor=BLUE_LIGHT,
    )
    add_box(
        ax,
        5.0,
        39.0,
        13.0,
        16.0,
        facecolor=WHITE,
        edgecolor="#94ABC1",
        title="结构化实例",
        body="任务集合\n候选骑手\n收益与接单意愿\n10 s 求解预算",
        title_color=BLUE,
        title_size=8.5,
        body_size=6.5,
    )

    add_container(
        ax,
        24.0,
        28.0,
        38.0,
        34.0,
        number="02",
        title="自适应搜索引擎",
        subtitle="Adaptive search engine",
        edgecolor=TEAL,
        facecolor=TEAL_LIGHT,
    )
    add_box(
        ax,
        27.0,
        47.5,
        14.0,
        8.2,
        facecolor=WHITE,
        edgecolor="#79A7A3",
        title="场景识别",
        body="规模 · 稀缺度 · 意愿度",
        title_color=TEAL,
        body_size=6.8,
    )
    add_box(
        ax,
        45.0,
        47.5,
        14.0,
        8.2,
        facecolor=WHITE,
        edgecolor="#79A7A3",
        title="候选生成",
        body="单任务 · 合单组合",
        title_color=TEAL,
        body_size=6.8,
    )
    add_box(
        ax,
        27.0,
        33.0,
        32.0,
        10.2,
        facecolor=WHITE,
        edgecolor="#79A7A3",
        title="多策略候选池",
        body="Greedy  ·  Matching  ·  Set Cover\nMin-Cost Flow  ·  Beam Search  ·  LNS",
        title_color=TEAL,
        body_size=7.0,
    )

    add_container(
        ax,
        65.5,
        28.0,
        32.0,
        34.0,
        number="03",
        title="证据门禁",
        subtitle="Evidence gate",
        edgecolor=GOLD,
        facecolor=GOLD_LIGHT,
    )
    add_box(
        ax,
        68.5,
        47.5,
        11.2,
        8.2,
        facecolor=WHITE,
        edgecolor="#C7A46D",
        title="快速评估",
        body="低成本筛选",
        title_color=GOLD,
        body_size=6.8,
    )
    add_box(
        ax,
        83.2,
        47.5,
        11.2,
        8.2,
        facecolor=WHITE,
        edgecolor="#C7A46D",
        title="精确评估",
        body="统一目标复算",
        title_color=GOLD,
        body_size=6.8,
    )
    add_box(
        ax,
        68.5,
        33.0,
        25.9,
        10.2,
        facecolor=WHITE,
        edgecolor="#C7A46D",
        title="合法性校验与质量门",
        body="输出协议 · 任务约束 · 骑手约束\n仅接受合法且更优的候选",
        title_color=GOLD,
        body_size=7.0,
    )

    # Directed evidence path.
    add_arrow(ax, (20.5, 48.0), (24.0, 48.0), color=BLUE, label="适配", label_xy=(22.2, 49.8))
    add_arrow(ax, (41.0, 51.6), (45.0, 51.6), color=TEAL)
    add_arrow(ax, (52.0, 47.5), (52.0, 43.2), color=TEAL)
    add_arrow(ax, (62.0, 38.2), (65.5, 38.2), color=TEAL, label="候选", label_xy=(63.7, 40.0))
    add_arrow(ax, (79.7, 51.6), (83.2, 51.6), color=GOLD)
    add_arrow(ax, (88.8, 47.5), (88.8, 43.2), color=GOLD)

    # Verified output and deterministic fallback form a separate, readable band.
    add_box(
        ax,
        65.5,
        17.3,
        32.0,
        7.5,
        facecolor=GREEN_LIGHT,
        edgecolor=GREEN,
        title="04  已验证的 best-so-far",
        body="格式化输出：任务组合 + 骑手列表",
        title_color=GREEN,
        body_size=7.1,
        title_size=8.8,
    )
    add_box(
        ax,
        24.0,
        17.3,
        38.0,
        7.5,
        facecolor=RED_LIGHT,
        edgecolor=RED,
        title="稳定性保障：确定性回退",
        body="超时 · 异常 · 质量门未通过时，仍返回合法结果",
        title_color=RED,
        body_size=7.0,
        title_size=8.8,
    )
    add_arrow(
        ax,
        (81.5, 33.0),
        (81.5, 24.8),
        color=GREEN,
        label="通过",
        label_xy=(84.2, 28.3),
    )
    add_arrow(ax, (62.0, 21.0), (65.5, 21.0), color=RED)
    add_elbow_arrow(
        ax,
        [(43.0, 33.0), (43.0, 26.5), (43.0, 24.8)],
        color=RED,
        label="预算耗尽 / 异常",
        label_xy=(49.5, 27.1),
    )

    # Bottom evidence loop: direct labels avoid a detached legend.
    ax.text(2.5, 13.6, "05  证据与记忆闭环", fontsize=9.8, fontweight=600, color=INK, va="center")
    ax.text(26.0, 13.6, "候选不能自报成绩，所有经验仍需重新通过同一门禁", fontsize=7.2, color=MUTED, va="center")
    add_box(
        ax,
        2.5,
        4.0,
        20.5,
        6.6,
        facecolor=NEUTRAL,
        edgecolor=LINE,
        title="决策轨迹",
        body="场景 · 候选 · 评分",
        title_size=8.2,
        body_size=6.6,
    )
    add_box(
        ax,
        27.3,
        4.0,
        20.5,
        6.6,
        facecolor=NEUTRAL,
        edgecolor=LINE,
        title="Critic 反馈",
        body="采纳 · 拒绝 · 失败原因",
        title_size=8.2,
        body_size=6.6,
    )
    add_box(
        ax,
        52.1,
        4.0,
        20.5,
        6.6,
        facecolor=NEUTRAL,
        edgecolor=LINE,
        title="Agent 记忆",
        body="结果回写 · 置信度更新",
        title_size=8.2,
        body_size=6.6,
    )
    add_box(
        ax,
        76.9,
        4.0,
        20.6,
        6.6,
        facecolor=BLUE_LIGHT,
        edgecolor=BLUE,
        title="下一轮策略先验",
        body="相似场景召回 · 时间片调整",
        title_color=BLUE,
        title_size=8.2,
        body_size=6.6,
    )
    add_arrow(ax, (23.0, 7.3), (27.3, 7.3), color=MUTED)
    add_arrow(ax, (47.8, 7.3), (52.1, 7.3), color=MUTED)
    add_arrow(ax, (72.6, 7.3), (76.9, 7.3), color=BLUE)
    add_elbow_arrow(
        ax,
        [(81.5, 17.3), (81.5, 12.2), (1.0, 12.2), (1.0, 7.3), (2.5, 7.3)],
        color=MUTED,
        linewidth=1.0,
        label="可审计证据",
        label_xy=(67.0, 12.2),
    )
    add_elbow_arrow(
        ax,
        [(97.5, 7.3), (98.7, 7.3), (98.7, 64.3), (22.5, 64.3), (22.5, 51.6), (27.0, 51.6)],
        color=BLUE,
        linewidth=1.0,
        label="只影响下一轮搜索",
        label_xy=(72.0, 64.3),
    )

    return fig


def export_figure(fig: plt.Figure, output_stem: Path) -> None:
    """Export editable vectors and a high-resolution GitHub preview."""
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    common = {"bbox_inches": "tight", "pad_inches": 0.08, "facecolor": WHITE}
    svg_path = output_stem.with_suffix(".svg")
    fig.savefig(svg_path, format="svg", **common)
    svg_text = svg_path.read_text(encoding="utf-8")
    svg_path.write_text("\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n", encoding="utf-8")
    fig.savefig(output_stem.with_suffix(".pdf"), format="pdf", **common)
    fig.savefig(output_stem.with_suffix(".png"), format="png", dpi=600, **common)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/assets/autosolver-system-architecture-v1"),
        help="Output path without an extension.",
    )
    args = parser.parse_args()
    figure = draw_figure()
    export_figure(figure, args.output)
    plt.close(figure)


if __name__ == "__main__":
    main()
