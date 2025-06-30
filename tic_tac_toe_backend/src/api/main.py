from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import init_db, get_db
from . import models, schemas

app = FastAPI(
    title="Tic Tac Toe Backend",
    description="Backend API for persistent Tic Tac Toe game with players and game history.",
    version="1.0.0",
    openapi_tags=[
        {"name": "game", "description": "Game session and move endpoints"},
        {"name": "player", "description": "Player management and history endpoints"},
    ],
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Initialize the database tables on startup."""
    init_db()


@app.get("/", tags=["system"])
def health_check():
    """Returns the health of the API."""
    return {"message": "Healthy"}


# PUBLIC_INTERFACE
@app.post(
    "/game/start",
    response_model=schemas.StartGameResponse,
    tags=["game"],
    summary="Start a new game",
    description="Creates a new game with two players, returns the game ID and player IDs.",
)
def start_game(req: schemas.StartGameRequest, db: Session = Depends(get_db)):
    def get_or_create_player(name):
        player = db.query(models.Player).filter(models.Player.name == name).first()
        if not player:
            player = models.Player(name=name)
            db.add(player)
            db.commit()
            db.refresh(player)
        return player

    player_x = get_or_create_player(req.player_x_name)
    player_o = get_or_create_player(req.player_o_name)

    game = models.Game(
        player_x_id=player_x.id,
        player_o_id=player_o.id,
        status=models.GameStatusEnum.ONGOING,
        winner=None,
    )
    db.add(game)
    db.commit()
    db.refresh(game)
    return schemas.StartGameResponse(
        game_id=game.id, player_x_id=player_x.id, player_o_id=player_o.id
    )


def get_game_board(game_moves):
    board = [None] * 9
    for move in sorted(game_moves, key=lambda m: m.turn):
        board[move.position] = move.symbol
    return board


def check_winner(board):
    lines = [
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),
        (0, 4, 8),
        (2, 4, 6),
    ]
    for a, b, c in lines:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    if all(board):
        return "draw"
    return None


# PUBLIC_INTERFACE
@app.post(
    "/game/move",
    response_model=schemas.MoveResponse,
    tags=["game"],
    summary="Make a move",
    description="Make a move in the current game. Returns updated board and status.",
)
def make_move(req: schemas.MoveRequest, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter(models.Game.id == req.game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if game.status == models.GameStatusEnum.COMPLETE:
        raise HTTPException(status_code=400, detail="Game is complete")

    player = db.query(models.Player).filter(models.Player.id == req.player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    moves = (
        db.query(models.Move)
        .filter(models.Move.game_id == game.id)
        .order_by(models.Move.turn)
        .all()
    )
    board = get_game_board(moves)
    if board[req.position] is not None:
        raise HTTPException(status_code=400, detail="Position already taken")

    turn = len(moves)
    if player.id == game.player_x_id:
        symbol = "X"
    elif player.id == game.player_o_id:
        symbol = "O"
    else:
        symbol = None
    if not symbol:
        raise HTTPException(status_code=400, detail="Player not in this game")

    # Basic rule enforcement
    if turn % 2 == 0 and symbol != "X":
        raise HTTPException(status_code=400, detail="It's X's turn")
    if turn % 2 == 1 and symbol != "O":
        raise HTTPException(status_code=400, detail="It's O's turn")

    move = models.Move(
        game_id=game.id,
        player_id=player.id,
        symbol=symbol,
        position=req.position,
        turn=turn + 1,
    )
    db.add(move)
    db.commit()

    moves = (
        db.query(models.Move)
        .filter(models.Move.game_id == game.id)
        .order_by(models.Move.turn)
        .all()
    )
    board = get_game_board(moves)
    winner = check_winner(board)
    if winner == "X":
        game.status = models.GameStatusEnum.COMPLETE
        game.winner = "X"
        db.commit()
    elif winner == "O":
        game.status = models.GameStatusEnum.COMPLETE
        game.winner = "O"
        db.commit()
    elif winner == "draw":
        game.status = models.GameStatusEnum.COMPLETE
        game.winner = None
        db.commit()

    return schemas.MoveResponse(
        status="complete" if game.status == models.GameStatusEnum.COMPLETE else "ongoing",
        winner=game.winner,
        board=board,
    )


# PUBLIC_INTERFACE
@app.get(
    "/game/state/{game_id}",
    response_model=schemas.GameStateResponse,
    tags=["game"],
    summary="Get game state",
    description="Returns the entire state of a game (board, moves, etc.)",
)
def get_game_state(game_id: int, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    moves = (
        db.query(models.Move)
        .filter(models.Move.game_id == game.id)
        .order_by(models.Move.turn)
        .all()
    )
    board = get_game_board(moves)
    move_infos = [
        schemas.MoveInfo(
            player_id=m.player_id,
            symbol=m.symbol,
            position=m.position,
            turn=m.turn,
            created_at=m.created_at,
        )
        for m in moves
    ]
    return schemas.GameStateResponse(
        game_id=game.id,
        status=game.status.value,
        board=board,
        winner=game.winner,
        moves=move_infos,
    )


# PUBLIC_INTERFACE
@app.get(
    "/game/history/{player_id}",
    response_model=schemas.GameHistoryResponse,
    tags=["player"],
    summary="Get player game history",
    description="Returns a player's game history",
)
def get_game_history(player_id: int, db: Session = Depends(get_db)):
    games_as_x = db.query(models.Game).filter(models.Game.player_x_id == player_id).all()
    games_as_o = db.query(models.Game).filter(models.Game.player_o_id == player_id).all()
    history = []
    for game in games_as_x:
        entry = schemas.GameHistoryEntry(
            game_id=game.id,
            started_at=game.created_at,
            status=game.status.value,
            player_symbol="X",
            winner=game.winner,
        )
        history.append(entry)
    for game in games_as_o:
        entry = schemas.GameHistoryEntry(
            game_id=game.id,
            started_at=game.created_at,
            status=game.status.value,
            player_symbol="O",
            winner=game.winner,
        )
        history.append(entry)
    history.sort(key=lambda g: g.started_at, reverse=True)
    return schemas.GameHistoryResponse(
        player_id=player_id,
        history=history,
    )
