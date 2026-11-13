#!/usr/bin/env python3
"""
Test executing 'write a code as txt' and 'open it' end-to-end.
"""

import sys
from pathlib import Path
import importlib.util

spec = importlib.util.spec_from_file_location("void_widget", "/run/media/prakash/TR_39/VOID/bin/void-widget.py")
void_widget = importlib.util.module_from_spec(spec)
sys.modules["void_widget"] = void_widget
spec.loader.exec_module(void_widget)

def test_execution_flow():
    print("=== Testing Execution Flow: 'write a code as txt' -> 'open it' ===")
    tool_hub = void_widget.DodaiosToolHub()
    engine = void_widget.AudioVoiceEngine(tool_hub)

    # 1. Execute 'write a code as txt'
    reply, badge, thumb = engine._execute_single_command("write a code as txt")
    print(f"[Step 1 Reply]:\n{reply}")
    print(f"[Step 1 Badge]: {badge}")
    print(f"[Step 1 Last Generated File]: {engine.last_generated_file}")
    print(f"[Step 1 ToolHub Last Created File]: {tool_hub.last_created_file}")

    assert engine.last_generated_file and Path(engine.last_generated_file).exists(), "Code file must exist on disk!"
    assert tool_hub.last_created_file == engine.last_generated_file, "ToolHub last_created_file must be synced!"

    # Verify content of generated file
    content = Path(engine.last_generated_file).read_text(encoding="utf-8")
    print(f"[File Size]: {len(content)} bytes")
    assert "def calculate_metrics" in content or "def main" in content, "Generated file must have valid code!"

    # 2. Execute follow-up 'open it'
    reply2, badge2, thumb2 = engine._execute_single_command("open it")
    print(f"\n[Step 2 Reply]: {reply2}")
    print(f"[Step 2 Badge]: {badge2}")
    assert "Opened code.txt" in reply2 or "Opened" in reply2, f"Should open the generated file, got: {reply2}"

    # 3. Test 'open that code'
    reply3, badge3, thumb3 = engine._execute_single_command("open that code")
    print(f"\n[Step 3 Reply]: {reply3}")
    assert "Opened" in reply3

    # 4. Test speech shortening on both replies
    speech1 = engine._clean_text_for_speech(reply)
    speech2 = engine._clean_text_for_speech(reply2)
    print(f"\n[Spoken Announcement 1]: '{speech1}'")
    print(f"[Spoken Announcement 2]: '{speech2}'")
    assert speech1 == "Created code file.", f"Expected 'Created code file.', got '{speech1}'"
    assert speech2 == "Opened file.", f"Expected 'Opened file.', got '{speech2}'"

    print("\nSUCCESS: End-to-end execution flow verified cleanly!")

if __name__ == "__main__":
    test_execution_flow()

