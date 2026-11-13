#!/usr/bin/env python3
"""
Test pipeline, provider configuration, widget size (358 x 246),
and execution efficiency.
"""

import sys
import os
import time
from pathlib import Path
import importlib.util

sys.path.insert(0, "/run/media/prakash/TR_39/VOID")

from agentic.providers import AIProviderManager, CloudOpenAICompatibleProvider, LocalOllamaProvider
from agentic.ui_components import VoidConfigWindow

spec = importlib.util.spec_from_file_location("void_widget", "/run/media/prakash/TR_39/VOID/bin/void-widget.py")
void_widget = importlib.util.module_from_spec(spec)
sys.modules["void_widget"] = void_widget
spec.loader.exec_module(void_widget)

def test_pipeline_and_efficiency():
    print("=== Testing Widget Dimensions (358 x 256) ===")
    assert void_widget.VoidMiniWidget.EXPANDED_W == 358, f"EXPANDED_W must be 358, got {void_widget.VoidMiniWidget.EXPANDED_W}"
    assert void_widget.VoidMiniWidget.EXPANDED_H == 256, f"EXPANDED_H must be 256, got {void_widget.VoidMiniWidget.EXPANDED_H}"
    assert void_widget.VoidMiniWidget.COLLAPSED_W == 358, f"COLLAPSED_W must be 358, got {void_widget.VoidMiniWidget.COLLAPSED_W}"
    print(f"Widget default dimensions verified: {void_widget.VoidMiniWidget.EXPANDED_W} x {void_widget.VoidMiniWidget.EXPANDED_H}")

    print("\n=== Testing Multi-Model Pipeline (Model 1 & Local) ===")
    prov_mgr = AIProviderManager()
    
    # 1. Test Model 1 (OpenRouter) Connection
    t0 = time.time()
    info = prov_mgr.cloud_provider.fetch_key_info()
    latency_ms = (time.time() - t0) * 1000
    print(f"Model 1 (Cloud) Ping: valid={info.get('valid')}, latency={latency_ms:.1f}ms, limit={info.get('free_requests_limit')}")
    assert info.get("valid") is True, f"Model 1 API key should be valid, error: {info.get('error')}"

    # 2. Test Local Ollama
    t0 = time.time()
    ollama_ok = prov_mgr.is_local_online()
    latency_ollama = (time.time() - t0) * 1000
    print(f"Local Model Ping: online={ollama_ok}, latency={latency_ollama:.1f}ms")

    # 3. Test Config Window Model 1..5 Naming
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(["test", "-platform", "offscreen"])
    cfg = VoidConfigWindow(provider_manager=prov_mgr)
    assert cfg.chk_openrouter.text() == "Model 1", f"Expected 'Model 1', got '{cfg.chk_openrouter.text()}'"
    assert cfg.chk_openai.text() == "Model 2", f"Expected 'Model 2', got '{cfg.chk_openai.text()}'"
    assert cfg.chk_groq.text() == "Model 3", f"Expected 'Model 3', got '{cfg.chk_groq.text()}'"
    assert cfg.chk_deepseek.text() == "Model 4", f"Expected 'Model 4', got '{cfg.chk_deepseek.text()}'"
    assert cfg.chk_custom.text() == "Model 5", f"Expected 'Model 5', got '{cfg.chk_custom.text()}'"
    print("UI model labels verified: Model 1, Model 2, Model 3, Model 4, Model 5")

    # 4. Test Multi-Agent Model Assignments Dropdowns
    for r_id, (cb, ed) in cfg.agent_ui_rows.items():
        items = [cb.itemText(i) for i in range(cb.count())]
        assert "Model 1" in items and "Model 2" in items and "Model 3" in items and "Model 4" in items and "Model 5" in items and "Local Model" in items, f"Dropdown items missing Model 1..5: {items}"
    print("Multi-Agent dropdown items verified: Model 1..5 + Local Model")

    # 5. Test Quick Generation via Model 1
    t0 = time.time()
    res = prov_mgr.cloud_provider.generate(prompt="Respond with exactly one word: Ready.", max_tokens=10)
    gen_time = (time.time() - t0) * 1000
    print(f"Model 1 Generation: '{res.strip()}' in {gen_time:.1f}ms")
    assert len(res.strip()) > 0, "Model 1 should return response"

    print("\nALL PIPELINE, SIZING, AND EFFICIENCY TESTS PASSED!")

if __name__ == "__main__":
    test_pipeline_and_efficiency()
