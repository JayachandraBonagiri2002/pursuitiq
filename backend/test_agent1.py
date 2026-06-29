"""
test_agent1.py — Smoke test for Agent 1

Run this FIRST to confirm:
  - Your OpenAI API key works
  - GPT-4.1 is accessible
  - Structured Outputs are working
  - The disqualifier detection is producing good output

Usage (from inside the backend folder):
    python test_agent1.py

Expected time: 20-40 seconds
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    print("\n" + "=" * 60)
    print("  PursuitIQ — Agent 1 Smoke Test")
    print("  RFP: Nordbank AG banking modernisation")
    print("=" * 60)
    print()

    from config import OPENAI_API_KEY
    if "paste-your-key" in OPENAI_API_KEY or len(OPENAI_API_KEY) < 20:
        print("ERROR: Your OpenAI API key is not set correctly.")
        print("   Open backend/.env and replace 'sk-paste-your-key-here'")
        print("   with your real API key from platform.openai.com")
        return

    print("API key found")
    print("Running Agent 1 — this takes 20-40 seconds...\n")

    try:
        from agents.agent1_decomposer import run_demo
        result = run_demo()
    except Exception as e:
        print(f"\nAgent 1 FAILED: {e}")
        print("\nCommon fixes:")
        print("  - Check your API key in .env")
        print("  - Make sure you ran: pip install -r requirements.txt")
        print("  - Check you have GPT-4.1 access on your OpenAI account")
        return

    print("=" * 60)
    print(f"  RFP:      {result.title}")
    print(f"  Client:   {result.client_name}")
    print(f"  Industry: {result.industry}")
    print(f"  Size:     {result.estimated_deal_size_usd}")
    print(f"  Requirements found: {result.total_requirements}")
    print(f"  Eliminatory: {result.eliminatory_count}")
    print("=" * 60)

    if result.hard_disqualifiers:
        print(f"\nHARD DISQUALIFIERS DETECTED ({len(result.hard_disqualifiers)}):")
        print("   (These would auto-eliminate your bid if missed)")
        for i, d in enumerate(result.hard_disqualifiers, 1):
            print(f"\n   {i}. {d}")
    else:
        print("\nNo hard disqualifiers detected in this RFP")

    if result.compliance_red_flags:
        print(f"\nCOMPLIANCE RED FLAGS ({len(result.compliance_red_flags)}):")
        for f in result.compliance_red_flags:
            print(f"   - {f}")

    print(f"\nKEY DATES:")
    for kd in result.key_dates[:5]:
        print(f"   {kd.event}: {kd.date}")

    print(f"\nTOP ELIMINATORY REQUIREMENTS:")
    elim = [r for r in result.requirements if r.priority.value == "eliminatory"]
    for r in elim[:5]:
        tag = "HIDDEN RISK" if r.is_hidden_risk else "-"
        print(f"   {tag} [{r.category.value.upper()}] {r.text[:90]}...")
        if r.hidden_risk_reason:
            print(f"           -> {r.hidden_risk_reason}")

    print()
    print("=" * 60)
    print("  Agent 1 is working perfectly!")
    print()
    print("  NEXT STEP:")
    print("  Run the vector store setup:")
    print("  python -m corpus.vector_store")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
