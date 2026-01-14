from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date

class LineItem(BaseModel):
    description: str = Field(..., description="Description of the item or service")
    quantity: Optional[float] = Field(None, description="Quantity of items")
    unit_price: Optional[float] = Field(None, description="Price per unit")
    amount: Optional[float] = Field(None, description="Total line item amount")

class InvoiceData(BaseModel):
    vendor_name: Optional[str] = Field(None, description="Name of the vendor/supplier")
    invoice_number: Optional[str] = Field(None, description="Invoice identifier")
    invoice_date: Optional[str] = Field(None, description="Date of the invoice (YYYY-MM-DD)")
    due_date: Optional[str] = Field(None, description="Payment due date (YYYY-MM-DD)")
    tax_amount: Optional[float] = Field(None, description="Total tax amount")
    total_amount: Optional[float] = Field(None, description="Total invoice amount including tax")
    currency: str = Field("USD", description="Currency code (e.g. USD, EUR)")
    line_items: List[LineItem] = Field(default_factory=list, description="List of items in the invoice")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "vendor_name": "Acme Corp",
                    "invoice_number": "INV-1001",
                    "invoice_date": "2023-10-25",
                    "total_amount": 150.00,
                    "line_items": [
                        {"description": "Widget A", "quantity": 10, "unit_price": 10.0, "amount": 100.0},
                        {"description": "Widget B", "quantity": 5, "unit_price": 10.0, "amount": 50.0}
                    ]
                }
            ]
        }
    }
