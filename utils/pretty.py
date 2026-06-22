def print_data_profile(profile: dict):
    print("\n" + "=" * 70)
    print("📊 DATA PROFILE SUMMARY")
    print("=" * 70)

    print(f"\n📦 Rows: {profile['row_count']}")
    print(f"📐 Columns: {len(profile['columns'])}")

    print("\n🔍 TOP NULL RATES (highest impact columns):")
    sorted_nulls = sorted(profile["null_rates"].items(), key=lambda x: x[1], reverse=True)

    for col, rate in sorted_nulls[:10]:
        print(f"  - {col:<25} : {rate:.2%}")

    print("\n🔑 MOST UNIQUE COLUMNS:")
    sorted_unique = sorted(profile["unique_counts"].items(), key=lambda x: x[1], reverse=True)

    for col, count in sorted_unique[:10]:
        print(f"  - {col:<25} : {count:,}")

    print("\n" + "=" * 70)


def print_gold_design(result: dict):
    print("\n" + "=" * 70)
    print("💡 GOLD LAYER DESIGN (AI GENERATED)")
    print("=" * 70)

    raw = result.get("raw_llm_output", "")

    try:
        # try to extract JSON block if present
        json_start = raw.find("[")
        json_end = raw.rfind("]") + 1

        parsed = json.loads(raw[json_start:json_end])

        for i, table in enumerate(parsed, 1):
            print(f"\n🏷️  Table {i}: {table['name']}")
            print(f"   Purpose: {table['purpose']}")

            print("   📊 Metrics:")
            for m in table.get("metrics", []):
                print(f"      - {m}")

    except Exception:
        # fallback: clean text output
        print("\n⚠️ Raw LLM Output:\n")
        print(raw)

    print("\n" + "=" * 70)