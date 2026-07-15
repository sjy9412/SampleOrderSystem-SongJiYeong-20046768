from models.todo_model import TodoModel
from views.todo_table_view import TodoTableView
from views.todo_summary_view import TodoSummaryView
from controllers.todo_controller import TodoController


def create_app(view_type: str = "table") -> TodoController:
    """
    Model, View, Controller 를 조립해 Controller 를 반환한다.
    view_type="table"   → TodoTableView  (상세 테이블)
    view_type="summary" → TodoSummaryView (요약 카운트)
    """
    model = TodoModel()
    if view_type == "summary":
        view = TodoSummaryView(model)
    else:
        view = TodoTableView(model)
    return TodoController(model, view)
