from typing import TypedDict, Optional

class AgentState(TypedDict):
    product_id:        int
    product_name:      str
    current_stock:     int
    threshold:         int
    reorder_qty:       int
    doi:               float
    forecast:          dict
    supplier_docs:     str
    decision:          dict
    confidence:        float
    po_reference:      str
    auto_executed:     bool
    notification_sent: bool
    error:             Optional[str]