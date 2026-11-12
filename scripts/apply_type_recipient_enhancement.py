import re
import py_compile

WIDGET_PATH = "/run/media/prakash/TR_39/VOID/bin/void-widget.py"

with open(WIDGET_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update recipient email prompt in _execute_single_command
old_prompt = 'return ("Who would you like to send the email to? Please tell me the recipient\'s email address.", "Prompt: Recipient", "")'
new_prompt = 'return ("Who would you like to send this email to? Please type the recipient\'s email address below, or speak it.", "Prompt: Recipient", "")'

assert old_prompt in content, "old_prompt not found"
content = content.replace(old_prompt, new_prompt, 1)

# 2. Update ask_user_clarification in _execute_ai_tool
old_clarif = '''            elif name == "ask_user_clarification":
                q = args.get("question", "Could you please clarify?")
                param = args.get("missing_param", "input")
                self._pending_action = {"type": param, "awaiting": param}
                return f"PROMPT_USER: {q}"'''

new_clarif = '''            elif name == "ask_user_clarification":
                q = args.get("question", "Could you please clarify?")
                param = args.get("missing_param", "input")
                self._pending_action = {"type": param, "awaiting": param}
                if "recipient" in param.lower() or "email" in param.lower():
                    q = "Who would you like to send this email to? Please type the recipient's email address below, or speak it."
                return f"PROMPT_USER: {q}"'''

assert old_clarif in content, "old_clarif not found"
content = content.replace(old_clarif, new_clarif, 1)

# 3. Update PROMPT_USER handling in Ollama response block
old_prompt_handling = '''                        if str(tool_result).startswith("PROMPT_USER:"):
                            prompt_q = str(tool_result).replace("PROMPT_USER:", "").strip()
                            return (prompt_q, "Prompt: User Clarification", "")'''

new_prompt_handling = '''                        if str(tool_result).startswith("PROMPT_USER:"):
                            prompt_q = str(tool_result).replace("PROMPT_USER:", "").strip()
                            badge = "Prompt: Recipient" if ("recipient" in prompt_q.lower() or "email" in prompt_q.lower()) else "Prompt: User Clarification"
                            return (prompt_q, badge, "")'''

assert old_prompt_handling in content, "old_prompt_handling not found"
content = content.replace(old_prompt_handling, new_prompt_handling, 1)

# 4. Enhance email recipient normalization in _pending_action
old_pending_rec = '''            p_type = p_action.get("type")
            if p_type in ["email_recipient", "recipient_email"]:
                rec_m = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", q_clean) or re.search(r"(?:to\s+)?([a-zA-Z0-9_.-]+)", q_clean)
                rec = rec_m.group(1).strip() if rec_m else q_clean.strip()'''

new_pending_rec = '''            p_type = p_action.get("type")
            if p_type in ["email_recipient", "recipient_email"]:
                norm_email = (
                    q_clean.strip()
                    .replace(" at ", "@")
                    .replace(" dot ", ".")
                    .replace(" dot com", ".com")
                    .replace(" dot org", ".org")
                    .replace(" dot net", ".net")
                    .replace(" dot io", ".io")
                )
                rec_m = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", norm_email) or re.search(r"(?:to\s+)?([a-zA-Z0-9_.-]+)", norm_email)
                rec = rec_m.group(1).strip() if rec_m else norm_email.strip()
                rec = rec.strip("<>\\\"' ,;:.")'''

assert old_pending_rec in content, "old_pending_rec not found"
content = content.replace(old_pending_rec, new_pending_rec, 1)

# 5. Update _on_response_ready to automatically focus and highlight the text input field
old_resp_ready = '''    def _on_response_ready(self, query: str, reply: str, badge: str, thumb: str) -> None:
        self.set_expanded(True)
        self._action_badge.setText(badge or "VOID")
        self._resp_text.setText(reply)
        if thumb and Path(thumb).exists():
            pix = QPixmap(thumb).scaled(220, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self._thumb_preview.setPixmap(pix)
            self._thumb_preview.setVisible(True)
        else:
            self._thumb_preview.setVisible(False)

    def _on_text_submitted(self) -> None:
        text = self._input_field.text().strip()
        if text:
            self._input_field.clear()
            self._query_bubble.setText(f\'💬 "{text}"\')
            self._query_bubble.setVisible(True)
            self._engine.execute_task(text)'''

new_resp_ready = '''    def _on_response_ready(self, query: str, reply: str, badge: str, thumb: str) -> None:
        self.set_expanded(True)
        self._action_badge.setText(badge or "VOID")
        self._resp_text.setText(reply)
        if thumb and Path(thumb).exists():
            pix = QPixmap(thumb).scaled(220, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self._thumb_preview.setPixmap(pix)
            self._thumb_preview.setVisible(True)
        else:
            self._thumb_preview.setVisible(False)

        # Automatically focus and highlight the text input field when clarification / input is requested
        if badge and "Prompt: Recipient" in badge:
            self.activateWindow()
            self._input_field.setPlaceholderText("Type recipient email (e.g. name@example.com)...")
            self._input_field.setStyleSheet("""
                QLineEdit {
                    background: rgba(56, 189, 248, 0.16);
                    border: 1.5px solid #38bdf8;
                    border-radius: 12px;
                    color: #ffffff;
                    font-size: 11px;
                    padding: 4px 10px;
                }
                QLineEdit:focus {
                    border: 2px solid #00f0ff;
                    background: rgba(56, 189, 248, 0.25);
                }
            """)
            self._input_field.setFocus()
        elif badge and "Prompt: Search Query" in badge:
            self.activateWindow()
            self._input_field.setPlaceholderText("Type search query...")
            self._input_field.setStyleSheet("""
                QLineEdit {
                    background: rgba(56, 189, 248, 0.16);
                    border: 1.5px solid #38bdf8;
                    border-radius: 12px;
                    color: #ffffff;
                    font-size: 11px;
                    padding: 4px 10px;
                }
                QLineEdit:focus {
                    border: 2px solid #00f0ff;
                    background: rgba(56, 189, 248, 0.25);
                }
            """)
            self._input_field.setFocus()
        else:
            self._input_field.setPlaceholderText('Ask VOID or type command...')
            self._input_field.setStyleSheet("""
                QLineEdit {
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.14);
                    border-radius: 12px;
                    color: #f8fafc;
                    font-size: 11px;
                    padding: 4px 10px;
                }
                QLineEdit:focus {
                    border: 1px solid rgba(56, 189, 248, 0.5);
                    background: rgba(255, 255, 255, 0.12);
                }
            """)

    def _on_text_submitted(self) -> None:
        text = self._input_field.text().strip()
        if text:
            self._input_field.clear()
            self._input_field.setPlaceholderText('Ask VOID or type command...')
            self._input_field.setStyleSheet("""
                QLineEdit {
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.14);
                    border-radius: 12px;
                    color: #f8fafc;
                    font-size: 11px;
                    padding: 4px 10px;
                }
                QLineEdit:focus {
                    border: 1px solid rgba(56, 189, 248, 0.5);
                    background: rgba(255, 255, 255, 0.12);
                }
            """)
            self._query_bubble.setText(f\'💬 "{text}"\')
            self._query_bubble.setVisible(True)
            self._engine.execute_task(text)'''

assert old_resp_ready in content, "old_resp_ready not found"
content = content.replace(old_resp_ready, new_resp_ready, 1)

# Write updated content
with open(WIDGET_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("[Apply] Successfully updated void-widget.py with type-in recipient email enhancement.")
py_compile.compile(WIDGET_PATH, doraise=True)
print("[Apply] Python syntax verification PASSED cleanly.")
