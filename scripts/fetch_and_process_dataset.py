#!/usr/bin/env python3
"""
Auto-Dataset Fetch & Processing Pipeline for Ultra-Lite AI Assistant
Streams exactly 1,500 rows of system/coding tasks and 1,500 rows of conversational data
using Hugging Face 'datasets' without downloading multi-gigabyte raw files.
Formats into standard ChatML JSONL and text training files.
"""
import os
import sys
import json
from pathlib import Path

DATA_DIR = Path("/run/media/prakash/TR_39/VOID/nano_brain_pipeline/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
JSONL_PATH = DATA_DIR / "nano_train_dataset.jsonl"
TXT_PATH = DATA_DIR / "nano_train_dataset.txt"

TARGET_CODING_ROWS = 1500
TARGET_CONVO_ROWS = 1500

def format_chatml(system_prompt: str, user_prompt: str, assistant_resp: str) -> str:
    return (
        f"<|im_start|>system\n{system_prompt.strip()}<|im_end|>\n"
        f"<|im_start|>user\n{user_prompt.strip()}<|im_end|>\n"
        f"<|im_start|>assistant\n{assistant_resp.strip()}<|im_end|>\n"
    )

def fetch_datasets():
    print("=" * 65)
    print("  STEP 2: AUTO-DATASET FETCH & PROCESSING PIPELINE")
    print(f"  Target: {TARGET_CODING_ROWS} Coding Rows + {TARGET_CONVO_ROWS} Conversational Rows")
    print("=" * 65)

    try:
        from datasets import load_dataset
    except ImportError:
        print("[Error] Hugging Face 'datasets' library is not yet installed.")
        sys.exit(1)

    combined_entries = []

    # 1. Fetch exactly 1,500 System & Coding Tasks (Streaming mode)
    print("\n[1/2] Streaming System & Coding Tasks (sahil2801/CodeAlpaca-20k)...")
    try:
        code_ds = load_dataset("sahil2801/CodeAlpaca-20k", split="train", streaming=True)
        count = 0
        for item in code_ds:
            if count >= TARGET_CODING_ROWS:
                break
            inst = item.get("instruction", "").strip()
            inp = item.get("input", "").strip()
            out = item.get("output", "").strip()
            if not inst or not out:
                continue

            user_msg = f"{inst}\nInput: {inp}" if inp else inst
            chatml_text = format_chatml(
                "You are an ultra-lite system & coding AI assistant running on AMD Ryzen 5700U.",
                user_msg,
                out
            )
            combined_entries.append({
                "type": "coding",
                "messages": [
                    {"role": "system", "content": "You are an ultra-lite system & coding AI assistant running on AMD Ryzen 5700U."},
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": out}
                ],
                "text": chatml_text
            })
            count += 1
            if count % 300 == 0:
                print(f"  -> Streamed {count}/{TARGET_CODING_ROWS} coding rows...")
        print(f"  ✓ Successfully captured exactly {count} coding tasks!")
    except Exception as e:
        print(f"  [Warning] Primary coding dataset stream error ({e}), trying fallback...")
        alt_ds = load_dataset("iamtarun/python_code_instructions_18k_alpaca", split="train", streaming=True)
        count = 0
        for item in alt_ds:
            if count >= TARGET_CODING_ROWS:
                break
            inst = item.get("instruction", "").strip()
            inp = item.get("input", "").strip()
            out = item.get("output", "").strip()
            if not inst or not out:
                continue
            user_msg = f"{inst}\n{inp}" if inp else inst
            chatml_text = format_chatml("You are an ultra-lite system & coding AI assistant.", user_msg, out)
            combined_entries.append({
                "type": "coding",
                "messages": [
                    {"role": "system", "content": "You are an ultra-lite system & coding AI assistant."},
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": out}
                ],
                "text": chatml_text
            })
            count += 1
        print(f"  ✓ Fallback captured {count} coding tasks!")

    # 2. Fetch exactly 1,500 Conversational / Assistant Tasks (Streaming mode)
    print("\n[2/2] Streaming Conversational Data (tatsu-lab/alpaca)...")
    try:
        convo_ds = load_dataset("tatsu-lab/alpaca", split="train", streaming=True)
        count = 0
        for item in convo_ds:
            if count >= TARGET_CONVO_ROWS:
                break
            inst = item.get("instruction", "").strip()
            inp = item.get("input", "").strip()
            out = item.get("output", "").strip()
            if not inst or not out:
                continue

            user_msg = f"{inst}\nContext: {inp}" if inp else inst
            chatml_text = format_chatml(
                "You are an ultra-lite, responsive assistant optimized for local execution.",
                user_msg,
                out
            )
            combined_entries.append({
                "type": "conversational",
                "messages": [
                    {"role": "system", "content": "You are an ultra-lite, responsive assistant optimized for local execution."},
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": out}
                ],
                "text": chatml_text
            })
            count += 1
            if count % 300 == 0:
                print(f"  -> Streamed {count}/{TARGET_CONVO_ROWS} conversational rows...")
        print(f"  ✓ Successfully captured exactly {count} conversational rows!")
    except Exception as e:
        print(f"  [Error streaming conversational data] {e}")
        sys.exit(1)

    print(f"\n[3/3] Writing {len(combined_entries)} total rows to storage...")
    # Write JSONL
    with open(JSONL_PATH, "w", encoding="utf-8") as f_jsonl, \
         open(TXT_PATH, "w", encoding="utf-8") as f_txt:
        for entry in combined_entries:
            f_jsonl.write(json.dumps(entry, ensure_ascii=False) + "\n")
            f_txt.write(entry["text"] + "\n")

    jsonl_mb = JSONL_PATH.stat().st_size / (1024 * 1024)
    txt_mb = TXT_PATH.stat().st_size / (1024 * 1024)
    print(f"  ✓ JSONL dataset saved: {JSONL_PATH} ({jsonl_mb:.2f} MB)")
    print(f"  ✓ Plaintext training file saved: {TXT_PATH} ({txt_mb:.2f} MB)")
    print("=" * 65)
    print(f"  DATASET READY: Exactly {len(combined_entries)} rows prepared (Zero bloat).")
    print("=" * 65)

if __name__ == "__main__":
    fetch_datasets()
