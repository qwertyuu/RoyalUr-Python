from enum import Enum
from typing import Optional


class PlayerType(Enum):
    """
    Represents the players of a game.
    """
    LIGHT = (1, "Light", 'L')
    """
    The light player.
    """

    DARK = (2, "Dark", 'D')
    """
    The dark player.
    """

    def __init__(self, value: int, name: str, character: str):
        self._value_ = value
        self.name = name
        self.character = character

    def get_other_player(self) -> 'PlayerType':
        """
        Retrieve the PlayerType representing the other player.
        """
        if self == PlayerType.LIGHT:
            return PlayerType.DARK
        elif self == PlayerType.DARK:
            return PlayerType.LIGHT
        else:
            raise ValueError(f"Unknown PlayerType {self}")

    @staticmethod
    def to_char(player: Optional['PlayerType']) -> str:
        """
        Convert the player to a single character.
        """
        return player.character if player else '.'


class Tile:
    """
    Represents a position on or off the board.
    """

    x: int
    """
    The x-coordinate of the tile. This coordinate is 1-based.
    """

    y: int
    """
    The y-coordinate of the tile. This coordinate is 1-based.
    """

    ix: int
    """
    The x-index of the tile. This coordinate is 0-based.
    """

    iy: int
    """
    The y-index of the tile. This coordinate is 0-based.
    """

    def __init__(self, x: int, y: int):
        if x < 1 or x > 26:
            raise ValueError(f"x must fall within the range [1, 26]. Invalid value: {x}")
        if y < 0:
            raise ValueError(f"y must not be negative. Invalid value: {y}");

        self.x = x
        self.y = y
        self.ix = x - 1
        self.iy = y - 1

    @staticmethod
    def from_indices(ix: int, iy: int) -> 'Tile':
        """
        Creates a new tile representing the tile at the
        indices (ix, iy), 0-based.
        """
        return Tile(ix + 1, iy + 1)

    def step_towards(self, other: 'Tile') -> 'Tile':
        """
        Takes a unit length step towards the other tile.
        """
        dx = other.x - self.x
        dy = other.y - self.y

        if abs(dx) + abs(dy) <= 1:
            return other

        if abs(dx) < abs(dy):
            return Tile(self.x, self.y + (1 if dy > 0 else -1))
        else:
            return Tile(self.x + (1 if dx > 0 else -1), self.y)

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False

        return self.x == other.x and self.y == other.y

    def __repr__(self) -> str:
        encoded_x = chr(self.x + (ord('A') - 1))
        return f"{encoded_x}{self.y}"

    def __str__(self) -> str:
        return repr(self)

    @staticmethod
    def from_string(encoded: str) -> 'Tile':
        """
        Decodes the tile coordinates from its encoded text (e.g., A4).
        """
        if len(encoded) < 2:
            raise ValueError("Incorrect format, expected at least two characters")

        x = ord(encoded[0]) - (ord('A') - 1)
        y = int(encoded[1:])
        return Tile(x, y)

    @staticmethod
    def create_list(*coordinates: list[tuple[int, int]]) -> list['Tile']:
        """
        Constructs a list of tiles from the tile coordinates.
        """
        return [Tile(x, y) for x, y in coordinates]

    @staticmethod
    def create_path(*coordinates: list[tuple[int, int]]) -> list['Tile']:
        """
        Constructs a path from waypoints on the board.
        """
        waypoints = Tile.create_list(coordinates)
        if len(waypoints) == 0:
            raise ValueError("No coordinates provided")

        path = [waypoints[0]]
        for index in range(1, len(waypoints)):
            current = waypoints[index - 1]
            next = waypoints[index]
            while current != next:
                current = current.step_towards(next)
                path.append(current)

        return path


class Piece:
    """
    A piece on a board.
    """

    owner: PlayerType
    """
    The player that owns this piece.
    """

    path_index: int
    """
    The index of the piece on its owner player's path.
    """

    def __init__(self, owner: PlayerType, path_index: int):
        if path_index < 0:
            raise ValueError(f"The path index cannot be negative: {path_index}")

        self.owner = owner
        self.path_index = path_index

    def __hash__(self) -> int:
        return hash((self.owner, self.path_index))

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False

        return self.owner == other.owner \
            and self.path_index == other.path_index

    @staticmethod
    def to_char(piece: Optional['Piece']) -> str:
        """
        Converts the given piece to a single character that can be used
        to textually represent the owner of a piece.
        """
        return PlayerType.to_char(piece.owner if piece is not None else None)


class Move:
    """
    A move that can be made on a board.
    """

    player: PlayerType
    """
    The instigator of this move.
    """

    source: Optional[Tile]
    """
    The origin of the move. If this is None, it represents
    that this move is introducing a new piece to the board.
    """

    source_piece: Optional[Piece]
    """
    The piece on the board to be moved, or None if this move
    is introducing a new piece to the board.
    """

    dest: Optional[Tile]
    """
    The destination of the move. If this is None, it represents
    that this move is scoring a piece.
    """

    dest_piece: Optional[Piece]
    """
    The piece to be placed at the destination, or None if
    this move is scoring a piece.
    """

    captured_piece: Optional[Piece]
    """
    The piece that will be captured by this move, or None if
    this move does not capture a piece.
    """

    def __init__(
            self,
            player: PlayerType,
            source: Optional[Tile],
            source_piece: Optional[Piece],
            dest: Optional[Tile],
            dest_piece: Optional[Piece],
            captured_piece: Optional[Piece],
    ):
        if (source is None) != (source_piece is None):
            raise ValueError("source and source_piece must either be both null, or both non-null")
        if (dest is None) != (dest_piece is None):
            raise ValueError("dest and dest_piece must either be both null, or both non-null")
        if dest is None and captured_piece is not None:
            raise ValueError("Moves without a destination cannot have captured a piece")

        self.player = player
        self.source = source
        self.source_piece = source_piece
        self.dest = dest
        self.dest_piece = dest_piece
        self.captured_piece = captured_piece

    def has_source(self) -> bool:
        """
        Determines whether this move is moving a piece on the board.
        """
        return self.source is not None

    def is_introducing_piece(self) -> bool:
        """
        Determines whether this move is moving a new piece onto the board.
        """
        return self.source is None

    def has_dest(self) -> bool:
        """
        Determines whether this moves a piece to a destination on the board.
        """
        return self.dest is not None

    def is_scoring_piece(self) -> bool:
        """
        Determines whether this move is moving a piece off of the board.
        """
        return self.dest is None

    def is_capture(self) -> bool:
        """
        Determines whether this move is capturing an existing piece on the board.
        """
        return self.captured_piece is not None

    def is_dest_rosette(self, shape: BoardShape) -> bool:
        """
        Determines whether this move will land a piece on a rosette. Under common
        rule sets, this will give another turn to the player.
        """
        return self.dest is not None and shape.is_rosette(self.dest)

    def get_source(self) -> Tile:
        """
        Gets the source piece of this move. If there is no source piece, in the
        case where a new piece is moved onto the board, this will throw an error.
        """
        if self.source is None:
            raise RuntimeError("This move has no source, as it is introducing a piece")

        return self.source

    def get_source_piece(self) -> Piece:
        """
        Gets the source piece of this move. If there is no source piece, in the
        case where a new piece is moved onto the board, this will throw an error.
        """
        if self.source_piece is None:
            raise RuntimeError("This move has no source, as it is introducing a piece")

        return self.source_piece

    def get_dest(self) -> Tile:
        """
        Gets the destination tile of this move. If there is no destination tile,
        in the case where a piece is moved off the board, this will throw an error.
        """
        if self.dest is None:
            raise RuntimeError("This move has no destination, as it is scoring a piece")

        return self.dest

    def get_dest_piece(self) -> Piece:
        """
        Gets the destination piece of this move. If there is no destination piece,
        in the case where a piece is moved off the board, this will throw an error.
        """
        if self.dest_piece is None:
            raise RuntimeError("This move has no destination, as it is scoring a piece")

        return self.dest_piece

    def get_captured_piece(self) -> Piece:
        """
        Gets the piece that will be captured by this move. If there is no piece
        that will be captured, this will throw an error.
        """
        if self.captured_piece is None:
            raise RuntimeError("This move does not capture a piece");

        return self.captured_piece

    def apply(self):
        # TODO : Need a Board implementation first
        pass

    def describe(self) -> str:
        """
        Generates an English description of this move.
        """
        scoring = self.is_scoring_piece()
        introducing = self.is_introducing_piece()

        if scoring and introducing:
            return "Introduce and score a piece."

        if scoring:
            return f"Score a piece from {self.get_source()}."

        builder = []
        if introducing:
            builder.append("Introduce a piece to ")
        else:
            builder.append(f"Move {self.get_source()} to ")

        if self.is_capture():
            builder.append("capture ")

        builder.append(f"{self.get_dest()}.")
        return "".join(builder)

    def __hash__(self) -> int:
        return hash((
            self.source, self.source_piece,
            self.dest, self.dest_piece,
            self.captured_piece
        ))

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False

        return self.source == other.source and self.source_piece == other.source_piece \
            and self.dest == other.dest and self.dest_piece == other.dest_piece \
            and self.captured_piece == other.captured_piece
