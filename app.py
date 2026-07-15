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
from controllers.order_controller import OrderController
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

    sample_ctrl     = SampleController(sample_model, SampleView(sample_model))
    order_ctrl      = OrderController(order_model, inventory_model, production_line, OrderView(order_model))
    monitoring_ctrl = MonitoringController(order_model, inventory_model, sample_model, MonitoringView())
    release_ctrl    = ReleaseController(order_model, ReleaseView(order_model))
    production_ctrl = ProductionController(production_line, ProductionView(production_line))

    return MainController([
        sample_ctrl,
        order_ctrl,
        monitoring_ctrl,
        release_ctrl,
        production_ctrl,
    ])
