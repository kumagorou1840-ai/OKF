from datetime import datetime
from pydantic import BaseModel, Field, computed_field

class ContractSchema(BaseModel):
    contract_id: str
    property_name: str
    room_number: str
    tenant_name: str
    current_rent: int
    new_rent: int
    renewal_date: str
    contact: str
    created_at: str = Field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    updated_at: str = Field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    initial_author: str = Field(default='Antigravity_Bot')
    last_editor: str = Field(default='Jev_Auditor')
    flag: str = Field(default='ACTIVE')
    memo: str = Field(default='特になし')

    @computed_field
    @property
    def rent_diff(self) -> int:
        return self.new_rent - self.current_rent
