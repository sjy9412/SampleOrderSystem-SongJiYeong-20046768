from models.sample import SampleModel
from models.order import OrderModel
from models.inventory import InventoryModel
from models.production_line import ProductionLine

from views.sample_view import SampleView
from views.order_view import OrderView
from views.monitoring_view import MonitoringView
from views.release_view import ReleaseView
from views.production_view import ProductionView

from controllers.sample_controller import SampleController
from controllers.order_controller import ReserveController
from controllers.approve_reject_controller import ApproveRejectController
from controllers.monitoring_controller import MonitoringController
from controllers.release_controller import ReleaseController
from controllers.production_controller import ProductionController
from controllers.main_controller import MainController


def create_app(view_type: str = "table") -> MainController:
    """Model, View, Controller 를 조립해 MainController 를 반환한다."""
    sample_model    = SampleModel()
    order_model     = OrderModel()
    inventory_model = InventoryModel()
    production_line = ProductionLine(order_model, inventory_model, sample_model)

    order_view      = OrderView(order_model)

    sample_ctrl         = SampleController(sample_model, inventory_model, SampleView(sample_model))
    reserve_ctrl        = ReserveController(order_model, order_view)
    approve_reject_ctrl = ApproveRejectController(order_model, inventory_model, production_line, order_view)
    monitoring_ctrl     = MonitoringController(order_model, inventory_model, sample_model, MonitoringView())
    production_ctrl     = ProductionController(production_line, ProductionView(production_line))
    release_ctrl        = ReleaseController(order_model, ReleaseView(order_model))

    return MainController(
        [
            sample_ctrl,         # 1. 시료 관리
            reserve_ctrl,        # 2. 시료 주문
            approve_reject_ctrl, # 3. 주문 승인/거절
            monitoring_ctrl,     # 4. 모니터링
            production_ctrl,     # 5. 생산라인 조회
            release_ctrl,        # 6. 출고 처리
        ],
        sample_model=sample_model,
        inventory_model=inventory_model,
        order_model=order_model,
        production_line=production_line,
    )
