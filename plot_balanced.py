
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data/balanced_sensitivity.csv")

fig, ax = plt.subplots(figsize=(9, 6))

ax.plot(
    df["total_cost_usd"],
    df["total_carbon_g"],
    marker="o"
)

for (cost, carbon), group in df.groupby(
    ["total_cost_usd", "total_carbon_g"]
):
    tolerances = ", ".join(
        f"{t:g}" for t in group["tolerance_usd"]
    )

    ax.annotate(
        f"tol={tolerances}",
        (cost, carbon),
        xytext=(7, 5),
        textcoords="offset points",
        fontsize=9
    )

ax.set_title("GreenPipeline - Cost vs Carbon")
ax.set_xlabel("Total Cost (USD)")
ax.set_ylabel("Estimated Carbon Emissions (gCO2e)")
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(
    "data/balanced_tradeoff.png",
    dpi=200,
    bbox_inches="tight"
)

plt.show()
