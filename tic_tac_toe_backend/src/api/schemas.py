from pydantic import BaseModel, Field
from typing import Optional, List
import enum
import datetime


class GameStatusEnum(str, enum.Enum):
    ongoing = "ongoing"
    complete = "complete"


class StartGameRequest(BaseModel):
    player_x_name: str = Field(..., description="Player X's name")
    player_o_name: str = Field(..., description="Player O's name")


class StartGameResponse(BaseModel):
    game_id: int = Field(..., description="Game ID")
    player_x_id: int
    player_o_id: int


class MoveRequest(BaseModel):
    game_id: int = Field(..., description="Game ID")
    player_id: int = Field(..., description="Player's ID")
    position: int = Field(..., description="Board position (0-8)")


class MoveResponse(BaseModel):
    status: str
    winner: Optional[str] = None
    board: List[Optional[str]] = Field(..., description="Current game board")


class MoveInfo(BaseModel):
    player_id: int
    symbol: str
    position: int
    turn: int
    created_at: datetime.datetime


class GameStateResponse(BaseModel):
    game_id: int
    status: GameStatusEnum
    board: List[Optional[str]]
    winner: Optional[str]
    moves: List[MoveInfo]


class GameHistoryEntry(BaseModel):
    game_id: int
    started_at: datetime.datetime
    status: GameStatusEnum
    player_symbol: str
    winner: Optional[str]


class GameHistoryResponse(BaseModel):
    player_id: int
    history: List[GameHistoryEntry]


GameStateResponse.update_forward_refs()
