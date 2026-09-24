"""Optional AI advice using only our heuristic, not Google review content.
Google editorial text is displayed verbatim separately; it is not sent to OpenAI.
"""
import os
import httpx
async def advice(estimate):
    key=os.getenv("OPENAI_API_KEY", "").strip()
    if not key: return None
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r=await client.post("https://api.openai.com/v1/responses",headers={"Authorization":"Bearer "+key},json={
                "model":os.getenv("OPENAI_MODEL","gpt-4.1-mini"),"store":False,"max_output_tokens":160,
                "instructions":"Write one friendly sentence of generic dining advice, maximum 35 words. The supplied crowd estimate is an unvalidated time heuristic. Never claim knowledge of a restaurant, reviews, staff language, actual crowds or reservations. Explicitly call it an estimate.",
                "input":"Time-based crowd estimate: "+estimate["label"]+". Reasons: "+", ".join(estimate["basis"])})
        r.raise_for_status()
        text=" ".join(c.get("text","") for o in r.json().get("output",[]) for c in o.get("content",[]) if c.get("type")=="output_text").strip()
        return text[:600] or None
    except (httpx.HTTPError,ValueError): return None
