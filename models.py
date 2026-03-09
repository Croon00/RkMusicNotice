from dataclasses import dataclass
'''
    여러줄 파이썬
'''

### BoothItem represents an item in the booth with its details. 
@dataclass
class BoothItem:
    item_id: int | None
    name: str | None
    price: str | None
    url: str | None
    image_url: str | None
    is_end_of_sale: bool | None
    is_sold_out: bool | None
    artist: str | None = None