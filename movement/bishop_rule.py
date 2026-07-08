from movement.path_checker import PathChecker


class BishopRule:

    def can_move(self, source, target, board):

        diagonal = (
            abs(target[0] - source[0])
            ==
            abs(target[1] - source[1])
        )


        return (
            diagonal
            and
            PathChecker.clear(
                board,
                source,
                target
            )
        )