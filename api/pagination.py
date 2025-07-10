import math
from flask_restx import abort
from flask import request
from sqlalchemy import select, func

def paginate(query, page: int, page_size: int, db):
    total_items = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    total_pages = max(1, math.ceil(total_items / page_size))
    if page > total_pages:
        return None, []
    rows = db.execute(query.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    meta = {
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "total_items": total_items,
    }
    return meta, rows

def get_pagination_params(api):
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 50))
        if page < 1 or page_size < 1 or page_size > 500:
            raise ValueError
    except (TypeError, ValueError):
        abort(400, "Invalid page or page_size parameter")
    return page, page_size