import re

active_workflows = {}

class WorkflowManager:
    @staticmethod
    def get_state(session_id):
        if session_id not in active_workflows:
            active_workflows[session_id] = {
                "state": "WAITING_ERROR_CODE",
                "context": {"error_code": None}
            }
        return active_workflows[session_id]

    @staticmethod
    def update_state(session_id, user_message, lower_msg):
        wf = WorkflowManager.get_state(session_id)
        ctx = wf["context"]

        match = re.search(r"RANA[-\s]?(\d{4})", user_message.upper())
        if not match:
            match = re.search(r"\b(\d{4})\b", user_message)

        if match:
            ctx["error_code"] = match.group(1)
            wf["state"] = "CODE_FOUND"
            return wf

        if any(w in lower_msg for w in ['bilmiyorum', 'nerden', 'nereden', 'bulamıyorum', 'nasıl', 'göremiyorum', 'nerede', 'kod']):
            wf["state"] = "WAITING_HOW_TO_FIND"
            return wf

        return wf