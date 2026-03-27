import time
from pytrends.request import TrendReq


def collect_trends(keywords: list[str], timeframe: str = "today 3-m") -> dict:
    print(f"Fetching Google Trends data for: {keywords}")
    result = {
        "interest_over_time": {},
        "related_topics": {},
        "related_queries": {},
        "rising_queries": {},
    }

    try:
        pytrends = TrendReq(hl="en-US", tz=360)
        pytrends.build_payload(keywords, timeframe=timeframe)
    except Exception as e:
        print(f"[google_trends] Failed to build payload: {e}")
        return result

    try:
        iot = pytrends.interest_over_time()
        if not iot.empty:
            iot = iot.drop(columns=["isPartial"], errors="ignore")
            result["interest_over_time"] = {
                col: iot[col].tolist() for col in iot.columns
            }
            result["interest_over_time"]["dates"] = [
                d.isoformat() for d in iot.index
            ]
    except Exception as e:
        print(f"[google_trends] interest_over_time failed: {e}")

    for kw in keywords:
        time.sleep(0.5)

        try:
            related = pytrends.related_topics()
            if kw in related:
                top = related[kw].get("top")
                rising = related[kw].get("rising")
                result["related_topics"][kw] = {
                    "top": top.to_dict("records") if top is not None and not top.empty else [],
                    "rising": rising.to_dict("records") if rising is not None and not rising.empty else [],
                }
        except Exception as e:
            print(f"[google_trends] related_topics for '{kw}' failed: {e}")

        try:
            queries = pytrends.related_queries()
            if kw in queries:
                top_q = queries[kw].get("top")
                rising_q = queries[kw].get("rising")
                result["related_queries"][kw] = (
                    top_q.to_dict("records") if top_q is not None and not top_q.empty else []
                )
                result["rising_queries"][kw] = (
                    rising_q.to_dict("records") if rising_q is not None and not rising_q.empty else []
                )
        except Exception as e:
            print(f"[google_trends] related_queries for '{kw}' failed: {e}")

    print("[google_trends] Done.")
    return result
