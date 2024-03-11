from typing import List, Dict, Any, Callable
from fastapi import HTTPException
import MySQLdb


async def callAPI(
    func: Callable, *args: List, **kwargs: Dict[str, Any]
) -> Dict[str, Any]:
    try:
        return await func(*args, **kwargs)
    except HTTPException as e:
        raise e
    except MySQLdb.Error as e:
        print(str(e))
        raise HTTPException(500, str(e))
    except Exception as e:
        # pdb.set_trace()
        print(str(e))
        raise HTTPException(500, str(e))
