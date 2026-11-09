
import pandas as pd

df = pd.read_csv(
    "data/benchmarks/real_docker_runtime_30.csv"
)

# İlk 20 gözlem: tahmin geliştirme
train = df["runtime_seconds"].iloc[:20]

# Son 10 gözlem: bağımsız test
test = df["runtime_seconds"].iloc[20:]

predictions = {
    "Mean": train.mean(),
    "P95": train.quantile(0.95),
    "Maximum": train.max()
}

print("\nGREENPIPELINE - SURE TAHMIN DOGRULAMASI")
print("Egitim olcumu:", len(train))
print("Test olcumu:", len(test))

for method, predicted in predictions.items():
    successful = (test <= predicted).sum()
    success_pct = successful / len(test) * 100

    print(f"\nYontem: {method}")
    print(f"Tahmin edilen sure: {predicted:.4f} s")
    print(f"Deadline'a yetisen: {successful}/{len(test)}")
    print(f"Basari orani: %{success_pct:.2f}")
