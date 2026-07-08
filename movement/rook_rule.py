from movement.movement_rule import MovementRule


class RookRule(MovementRule):

    def can_move(self, source, target):

        return (
            source[0] == target[0]
            or
            source[1] == target[1]
        )