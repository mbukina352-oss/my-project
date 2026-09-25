from dataclasses import dataclass


@dataclass
class Flat:
    complex_name: str = ""
    address: str = ""
    building: str = ""
    rooms: int | None = None  # 0 = студия
    area: float | None = None
    floor: str = ""
    price: int | None = None
    deadline: str = ""
    finishing: str = ""
    plan_url: str = ""
    plan_image: bytes | None = None  # PNG/JPEG планировки

    @property
    def rooms_label(self) -> str:
        if self.rooms is None:
            return ""
        return "Студия" if self.rooms == 0 else f"{self.rooms}-комнатная"
