from movement.path_checker import PathChecker


class RookRule:


    def can_move(self, source, target, board):

        straight = (
            source[0] == target[0]
            or
            source[1] == target[1]
        )

        return (
            straight
            and
            PathChecker.clear(
                board,
                source,
                target
            )
        )