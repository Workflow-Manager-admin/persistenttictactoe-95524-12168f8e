from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Enum
)
from sqlalchemy.orm import declarative_base, relationship
import enum
import datetime


Base = declarative_base()


class GameStatusEnum(str, enum.Enum):
    ONGOING = "ongoing"
    COMPLETE = "complete"


class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)


class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, index=True)
    player_x_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    player_o_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    status = Column(Enum(GameStatusEnum), default=GameStatusEnum.ONGOING)
    winner = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    player_x = relationship("Player", foreign_keys=[player_x_id])
    player_o = relationship("Player", foreign_keys=[player_o_id])
    moves = relationship("Move", back_populates="game")


class Move(Base):
    __tablename__ = "moves"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    position = Column(Integer, nullable=False)  # 0-8 for board positions
    turn = Column(Integer, nullable=False)
    symbol = Column(String, nullable=False)  # "X" or "O"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    game = relationship("Game", back_populates="moves")
    player = relationship("Player")
