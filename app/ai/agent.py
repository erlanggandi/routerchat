import logging
from typing import Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from app.ai.factory import get_llm
from app.ai.prompts import SYSTEM_PROMPT
from app.ai.tools import build_tools
from app.mikrotik.service import MikrotikService
from app.database.models import Router

logger = logging.getLogger(__name__)


class MikrotikAIAgent:
    def __init__(self):
        pass

    async def run(
        self,
        user_message: str,
        service: MikrotikService,
        db: AsyncSession,
        user_id: int,
        router: Router,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Executes AI reasoning with router-bound tools.
        Returns:
            (final_reply_text, list_of_pending_proposals)
        """
        tools_list, pending_proposals = build_tools(service, db, user_id, router)
        tools_by_name = {t.name: t for t in tools_list}

        llm = get_llm()
        llm_with_tools = llm.bind_tools(tools_list)

        system_instruction = (
            f"{SYSTEM_PROMPT}\n\n"
            f"INFORMASI ROUTER AKTIF SAAT INI:\n"
            f"- Nama Router: {router.name}\n"
            f"- Host: {router.host}:{router.port}\n"
            f"- Deskripsi: {router.description or '-'}\n"
        )

        messages = [
            SystemMessage(content=system_instruction),
            HumanMessage(content=user_message),
        ]

        # Max 5 iterative tool turns to prevent infinite loops
        for step in range(5):
            try:
                ai_msg = await llm_with_tools.ainvoke(messages)
            except Exception as e:
                logger.error(f"Error invoking LLM: {e}")
                return (
                    f"⚠️ Gagal berkomunikasi dengan AI Provider: {str(e)}\n\n"
                    f"Pastikan `AI_BASE_URL` dan `AI_API_KEY` di file `.env` sudah benar dan aktif.",
                    [],
                )

            messages.append(ai_msg)

            if not ai_msg.tool_calls:
                # No more tools requested, reply to user
                return ai_msg.content, pending_proposals

            # Process tool calls
            for tool_call in ai_msg.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]

                selected_tool = tools_by_name.get(tool_name)
                if selected_tool:
                    try:
                        tool_result = await selected_tool.ainvoke(tool_args)
                    except Exception as err:
                        tool_result = f"Error executing tool {tool_name}: {str(err)}"
                else:
                    tool_result = f"Tool '{tool_name}' not found."

                messages.append(
                    ToolMessage(
                        content=str(tool_result),
                        name=tool_name,
                        tool_call_id=tool_id,
                    )
                )

        # Fallback if iterations exceed limit
        return messages[-1].content if messages else "Selesai memproses.", pending_proposals


ai_agent = MikrotikAIAgent()
