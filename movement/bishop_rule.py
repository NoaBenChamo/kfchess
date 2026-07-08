from movement.movement_rule import MovementRule


class BishopRule(MovementRule):

    def can_move(self, source, target):

        return (
            abs(target[0] - source[0])
            ==
            abs(target[1] - source[1])
        )