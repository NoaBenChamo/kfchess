from realtime.clock import GameClock
from realtime.movement_validator import MovementValidator

from rules.capture_rule import CaptureRule
from rules.game_over_rule import GameOverRule
from rules.promotion_rule import PromotionRule


class RealTimeArbiter:


    def __init__(self, board):

        self._board = board

        self._clock = GameClock()

        self._active_moves = []

        self._active_jumps = []

        self._game_events = []



    def add_move(self, move):

        self._active_moves.append(move)



    def wait(self, ms):

        self._clock.advance(ms)

        self.resolve_finished_moves()

        self.resolve_finished_jumps()



    def get_time(self):

        return self._clock.get_time()



    def is_moving(self, position):

        return MovementValidator.is_moving(
            self._active_moves,
            position
        )



    def resolve_finished_moves(self):

        current_time = self._clock.get_time()

        finished = []


        for move in self._active_moves:

            if move.is_finished(current_time):

                finished.append(move)


        self.resolve_collisions(finished)


        for move in finished:

            if move in self._active_moves:

                self._active_moves.remove(move)


    def resolve_move(self, move):

        print(
            "MOVE:",
            move.piece,
            "arrival:",
            move.arrival_time
        )

        collision = None

        for other in self._active_moves:

            if other == move:
                continue


            if other.target == move.target:

                collision = other
                break



        if collision is None:

            self.finish_move(move)

            return



        # כלים בצבעים שונים:
        if move.piece.color != collision.piece.color:


            if move.arrival_time >= collision.arrival_time:

                self.finish_move(move)

            else:

                self.finish_move(collision)



        # כלים באותו צבע:
        else:

            if move.arrival_time > collision.arrival_time:

                return

            else:

                self.finish_move(move)



    def finish_move(self, move):

        target_piece = self._board.get(
            move.target
        )


        if target_piece is not None:

            if not CaptureRule.can_capture(
                move.piece,
                target_piece
            ):

                return



        self._board.set(
            move.source,
            None
        )


        self._board.set(
            move.target,
            move.piece
        )



        if PromotionRule.should_promote(
            move.piece,
            move.target,
            self._board
        ):

            move.piece.type = "Q"



        if GameOverRule.is_king_captured(
            target_piece
        ):

            self._game_events.append(
                "GAME_OVER"
            )



    def resolve_finished_jumps(self):

        current_time = self._clock.get_time()

        finished = []


        for jump in self._active_jumps:

            if jump.is_finished(current_time):

                finished.append(jump)



        for jump in finished:

            self._active_jumps.remove(jump)



    def get_events(self):

        events = self._game_events[:]

        self._game_events.clear()

        return events
    

    def is_piece_moving(self, position):

        for move in self._active_moves:

            if move.source == position:
                return True

        return False
    


    def resolve_collisions(self, moves):

        handled = set()


        for move in moves:

            if move in handled:
                continue


            opponent = None


            for other in moves:

                if other == move:
                    continue


                if other.target == move.target:

                    opponent = other
                    break


            if opponent is None:

                self.finish_move(move)
                handled.add(move)
                continue


            # צבעים שונים
            if move.piece.color != opponent.piece.color:

                if move.arrival_time > opponent.arrival_time:

                    self.finish_move(move)

                else:

                    self.finish_move(opponent)


            # אותו צבע
            else:

                if move.arrival_time < opponent.arrival_time:

                    self.finish_move(move)


            handled.add(move)
            handled.add(opponent)