import io
import matplotlib
# Use non-interactive Agg backend
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def generate_resource_chart(
    router_name: str,
    cpu_load: int,
    mem_usage_pct: float,
    used_mem_mb: float,
    free_mem_mb: float,
) -> io.BytesIO:
    """Generate a clean visual chart for CPU & Memory usage."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.8), facecolor="#1e1e2e")
    
    # 1. Bar Chart: CPU & RAM Percentage
    categories = ["CPU Load", "RAM Usage"]
    values = [cpu_load, mem_usage_pct]
    colors = ["#ff5555" if cpu_load > 80 else "#50fa7b", "#ffb86c" if mem_usage_pct > 80 else "#8be9fd"]

    bars = ax1.bar(categories, values, color=colors, width=0.5, edgecolor="#6272a4", linewidth=1.5)
    ax1.set_ylim(0, 100)
    ax1.set_ylabel("Penggunaan (%)", color="#f8f8f2")
    ax1.set_title(f"Beban Sistem ({router_name})", color="#f8f8f2", fontsize=11, fontweight="bold")
    ax1.tick_params(colors="#f8f8f2")
    ax1.set_facecolor("#282a36")
    ax1.grid(axis="y", linestyle="--", alpha=0.3, color="#6272a4")

    for bar in bars:
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 2,
            f"{height:.1f}%",
            ha="center",
            va="bottom",
            color="#f8f8f2",
            fontweight="bold",
        )

    # 2. Donut / Pie Chart: RAM Distribution
    ram_labels = [f"Used ({used_mem_mb:.1f} MB)", f"Free ({free_mem_mb:.1f} MB)"]
    ram_sizes = [used_mem_mb, free_mem_mb]
    pie_colors = ["#ff5555" if mem_usage_pct > 80 else "#bd93f9", "#44475a"]
    
    wedges, texts, autotexts = ax2.pie(
        ram_sizes,
        labels=ram_labels,
        autopct="%1.1f%%",
        startangle=140,
        colors=pie_colors,
        textprops={"color": "#f8f8f2"},
        wedgeprops={"edgecolor": "#282a36", "linewidth": 2, "width": 0.5},
    )
    for autotext in autotexts:
        autotext.set_color("#f8f8f2")
        autotext.set_fontweight("bold")
    ax2.set_title("Distribusi RAM", color="#f8f8f2", fontsize=11, fontweight="bold")

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=130, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_traffic_chart(
    interface_name: str,
    rx_mbps: float,
    tx_mbps: float,
    rx_pps: int,
    tx_pps: int,
) -> io.BytesIO:
    """Generate a clean visual bar chart for RX / TX traffic."""
    fig, ax = plt.subplots(figsize=(6, 3.5), facecolor="#1e1e2e")
    
    labels = ["Download (RX)", "Upload (TX)"]
    rates = [rx_mbps, tx_mbps]
    colors = ["#50fa7b", "#ff79c6"]

    bars = ax.barh(labels, rates, color=colors, height=0.4, edgecolor="#6272a4", linewidth=1.5)
    ax.set_xlabel("Kecepatan (Mbps)", color="#f8f8f2")
    ax.set_title(f"Trafik Interface: {interface_name}", color="#f8f8f2", fontsize=12, fontweight="bold")
    ax.tick_params(colors="#f8f8f2")
    ax.set_facecolor("#282a36")
    ax.grid(axis="x", linestyle="--", alpha=0.3, color="#6272a4")

    # Add text labels on bars
    for bar, rate, pps in zip(bars, rates, [rx_pps, tx_pps]):
        width = bar.get_width()
        ax.text(
            width + 0.05,
            bar.get_y() + bar.get_height() / 2.0,
            f"{rate:.2f} Mbps ({pps} pps)",
            ha="left",
            va="center",
            color="#f8f8f2",
            fontweight="bold",
        )

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=130, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf
