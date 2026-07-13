from config.constants import VALID_TOKENS


class BoardValidator:

    # בודק שכל הכלים בלוח חוקיים  
    @staticmethod
    def validate(cells):

        for row in cells:

            for token in row:

                if token not in VALID_TOKENS:
                    return False
                
        return True