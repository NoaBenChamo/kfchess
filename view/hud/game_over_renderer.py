class GameOverRenderer:
    """
    Draws the game over overlay.
    """

    def render(self, canvas):
        """
        Draws the game over message on top of the current canvas.
        """
        height, width = canvas.img.shape[:2]

        font_scale = max(
            1.0,
            width / 400.0,
        )

        canvas.put_text(
            "GAME OVER",
            width // 4,
            height // 2,
            font_scale,
            color=(0, 0, 255, 255),
            thickness=4,
        )