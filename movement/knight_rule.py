from movement.movement_rule import MovementRule


class KnightRule(MovementRule):

    def can_move(self, source, target, board):

        row = abs(target[0] - source[0])
        col = abs(target[1] - source[1])

        return (
            (row == 2 and col == 1)
            or
            (row == 1 and col == 2)
        )
    
